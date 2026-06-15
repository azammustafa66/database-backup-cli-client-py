import gzip
import os
import subprocess
import threading
from typing import IO

import psycopg


def build_postgres_args(config: dict) -> list[str]:
    # Password is passed via the PGPASSWORD env var (see _pg_env), not on the command line.
    args: list[str] = []
    if config.get('host'):
        args.append(f'--host={config["host"]}')
    if config.get('port'):
        args.append(f'--port={config["port"]}')
    if config.get('user'):
        args.append(f'--username={config["user"]}')
    return args


def _pg_env(config: dict) -> dict[str, str]:
    # pg_dump and psql read the password from PGPASSWORD rather than accepting it as an argument.
    env = os.environ.copy()
    if config.get('password'):
        env['PGPASSWORD'] = config['password']
    return env


def _drain(stream: IO[bytes]) -> threading.Thread:
    """Print a process pipe line-by-line on a background thread so it never fills and deadlocks."""

    def run() -> None:
        for raw in iter(stream.readline, b''):
            line = raw.decode(errors='replace').rstrip()
            if line:
                print(line)
        stream.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def connect_to_postgres(config: dict) -> None:
    connection = None
    try:
        print('Connecting to PostgreSQL...')
        connection = psycopg.connect(
            host=config.get('host'),
            port=int(config['port']) if config.get('port') else 5432,
            user=config.get('user') or None,
            password=config.get('password') or None,
            dbname=config.get('database_name'),
        )
        print('Successfully connected to PostgreSQL.')
    except Exception as error:
        print(f'Connection to PostgreSQL failed: {error}')
        raise
    finally:
        if connection is not None:
            connection.close()


def execute_postgres_dump(config: dict) -> None:
    print('Starting pg_dump...')

    # --no-owner / --no-privileges drop OWNER and GRANT statements so the dump restores cleanly as a
    # different user (the Postgres analog to stripping MySQL's DEFINER clauses).
    args = ['--no-owner', '--no-privileges', *build_postgres_args(config)]
    if config.get('database_name'):
        args.append(config['database_name'])

    out_path = os.path.join(config['out'], f'{config.get("database_name")}-backup.sql.gz')

    try:
        dump_process = subprocess.Popen(
            ['pg_dump', *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_pg_env(config),
        )
    except FileNotFoundError as error:
        raise RuntimeError(f'Failed to start pg_dump: {error}') from error

    assert dump_process.stdout is not None and dump_process.stderr is not None
    stderr_thread = _drain(dump_process.stderr)

    # pg_dump's plain-SQL stdout is gzip-compressed on the fly straight into the backup file.
    try:
        with gzip.open(out_path, 'wb') as gz:
            for chunk in iter(lambda: dump_process.stdout.read(65536), b''):
                gz.write(chunk)
    except OSError as error:
        dump_process.kill()
        raise RuntimeError(f'Failed to write backup: {error}') from error
    finally:
        dump_process.stdout.close()

    code = dump_process.wait()
    stderr_thread.join()
    if code != 0:
        raise RuntimeError(f'pg_dump exited with code {code}')


def execute_postgres_restore(config: dict) -> None:
    print('Starting PostgreSQL restore...')

    # ON_ERROR_STOP makes psql exit non-zero on the first SQL error so failures surface here.
    args = ['--set=ON_ERROR_STOP=on', *build_postgres_args(config)]
    if config.get('database_name'):
        args.append(f'--dbname={config["database_name"]}')

    file_path = os.path.join(config['out'], f'{config.get("database_name")}-backup.sql.gz')
    if not os.path.exists(file_path):
        raise RuntimeError(f'Could not read backup file at {file_path}')

    try:
        restore_process = subprocess.Popen(
            ['psql', *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_pg_env(config),
        )
    except FileNotFoundError as error:
        raise RuntimeError(f'Failed to start psql: {error}') from error

    assert (
        restore_process.stdin is not None
        and restore_process.stdout is not None
        and restore_process.stderr is not None
    )
    out_thread = _drain(restore_process.stdout)
    err_thread = _drain(restore_process.stderr)

    # Decompress the backup on the fly and feed the SQL straight into psql's stdin.
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8', errors='replace') as gz:
            for line in gz:
                try:
                    restore_process.stdin.write(line.encode())
                except BrokenPipeError:
                    # psql exited early with an error; the real cause is captured via the exit code.
                    break
    finally:
        try:
            restore_process.stdin.close()
        except BrokenPipeError:
            pass

    code = restore_process.wait()
    out_thread.join()
    err_thread.join()
    if code != 0:
        raise RuntimeError(f'psql restore exited with code {code}')
