# DB Backup CLI

An interactive command-line tool for backing up and restoring **MongoDB** and
**PostgreSQL** databases. It guides you through connection details step by step,
then delegates to the native database tools (`mongodump`, `pg_dump`, etc.) to
perform the actual operation.

This is a Python port of the original Bun/TypeScript version.

## Prerequisites

The following CLI tools must be installed and available in your `PATH`:

| Tool           | Used for           |
| -------------- | ------------------ |
| `mongodump`    | MongoDB backup     |
| `mongorestore` | MongoDB restore    |
| `pg_dump`      | PostgreSQL backup  |
| `psql`         | PostgreSQL restore |

Install MongoDB tools from the [MongoDB Database Tools][mongo-tools] page.
Install PostgreSQL client tools via your package manager (`brew install libpq`
or `brew install postgresql` on macOS).

[mongo-tools]: https://www.mongodb.com/try/download/database-tools

## Installation

This project uses [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Usage

```bash
uv run python main.py
```

or, after installing, via the console script:

```bash
uv run db-backup
```

The wizard will ask you:

1. **Action** — Backup or Restore
2. **Database engine** — MongoDB or PostgreSQL
3. **Output / input path** — where to save or read backups from
   (default: `./backups`)
4. **Connection details** — host/port/credentials, or a full URI for MongoDB

### Backup output files

| Engine     | File                             |
| ---------- | -------------------------------- |
| MongoDB    | `<out>/mongo-backup.archive.gz`  |
| PostgreSQL | `<out>/<database>-backup.sql.gz` |

## Project structure

```text
main.py                   # Entry point — top-level menu
src/
  cli/
    prompts.py            # All interactive prompts (questionary)
  commands/
    backup.py             # Backup flow orchestration
    restore.py            # Restore flow orchestration
  db/
    mongo.py              # MongoDB connect / dump / restore
    postgres.py           # PostgreSQL connect / dump / restore
  utils/
    spawn.py              # Shared child-process wrapper
```

Connection details gathered from the prompts are passed around as a plain `dict`.

## Inspiration

Built as part of the [Database Backup Utility][project] project on
[roadmap.sh][roadmap].

[project]: https://roadmap.sh/projects/database-backup-utility
[roadmap]: https://roadmap.sh

## Notes

- Passwords are hidden during input and passed to `pg_dump`/`psql` via the
  `PGPASSWORD` environment variable.
- MongoDB restore uses `--drop`, which drops existing collections before
  restoring to prevent duplicate-key conflicts.
- PostgreSQL backups use `pg_dump --no-owner --no-privileges` so they restore
  cleanly as a different user, and are gzip-compressed on the fly; restores
  decompress on the fly and pipe into `psql` with `ON_ERROR_STOP` enabled.
- `connect_to_mongo` and `connect_to_postgres` are pre-flight connectivity
  checks only. The actual data transfer is handled by the native CLI tools.
