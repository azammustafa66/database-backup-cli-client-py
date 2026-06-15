from pymongo import MongoClient

from src.utils.spawn import run_process


def construct_mongo_uri(
    host: str | None,
    port: str | None,
    user: str | None,
    password: str | None,
) -> str:
    if user and password:
        return f'mongodb://{user}:{password}@{host}:{port}'
    return f'mongodb://{host}:{port}'


def build_mongo_args(config: dict) -> list[str]:
    if config.get('uri'):
        return [f'--uri={config["uri"]}']

    args: list[str] = []
    if config.get('host'):
        args.append(f'--host={config["host"]}')
    if config.get('port'):
        args.append(f'--port={config["port"]}')
    if config.get('user'):
        args.append(f'--username={config["user"]}')
    if config.get('password'):
        args.append(f'--password={config["password"]}')
    return args


# Pre-flight connectivity check only. The actual data transfer is handled by the mongodump/mongorestore
# CLI tools which open their own connection, so this client is closed immediately in finally.
def connect_to_mongo(config: dict) -> None:
    uri = config.get('uri') or construct_mongo_uri(
        config.get('host'), config.get('port'), config.get('user'), config.get('password')
    )
    client: MongoClient | None = None
    try:
        print('Connecting to MongoDB...')
        client = MongoClient(uri, compressors='zlib')
        # MongoClient connects lazily, so issue a command to force an actual connection.
        client.admin.command('ping')
        print('Successfully connected to MongoDB.')
    except Exception as error:
        print(f'Connection to MongoDB failed: {error}')
        raise
    finally:
        if client is not None:
            client.close()


def execute_mongo_dump(config: dict) -> None:
    print('Starting mongodump...')
    run_process(
        'mongodump',
        [
            f'--archive={config["out"]}/mongo-backup.archive.gz',
            '--gzip',
            *build_mongo_args(config),
        ],
    )


def execute_mongo_restore(config: dict) -> None:
    print('Starting mongorestore...')
    run_process(
        'mongorestore',
        [
            f'--archive={config["out"]}/mongo-backup.archive.gz',
            '--gzip',
            '--drop',  # drop existing collections before restoring to avoid duplicate-key conflicts
            *build_mongo_args(config),
        ],
    )
