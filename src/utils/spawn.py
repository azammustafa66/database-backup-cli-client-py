import subprocess


def run_process(command: str, args: list[str]) -> None:
    """Run a child process, streaming its output live, and raise on a non-zero exit.

    stderr is merged into stdout because mongodump and mongorestore write their progress to
    stderr, not stdout, so we log it as info rather than treating it as an error.
    """
    try:
        proc = subprocess.Popen(
            [command, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as error:
        raise RuntimeError(f'Failed to start {command}: {error}') from error

    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            print(line)

    code = proc.wait()
    if code != 0:
        raise RuntimeError(f'{command} exited with code {code}')
