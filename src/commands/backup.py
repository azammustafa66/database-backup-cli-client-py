import os

import questionary

from src.cli.prompts import (prompt_db_type, prompt_mongo_credentials,
                             prompt_postgres_credentials)
from src.db.mongo import connect_to_mongo, execute_mongo_dump
from src.db.postgres import connect_to_postgres, execute_postgres_dump


def handle_backup_flow() -> None:
    db_type = prompt_db_type()
    config = {'type': db_type}

    config['out'] = questionary.text(
        'Where should we save the backup?',
        default='./backups',
    ).unsafe_ask()

    if db_type == 'mongodb':
        prompt_mongo_credentials(config)
    else:
        prompt_postgres_credentials(config)

    print('\n=========================================')
    print('Initiating Backup Process...')
    print('=========================================\n')

    os.makedirs(config['out'], exist_ok=True)

    if db_type == 'mongodb':
        connect_to_mongo(config)
        execute_mongo_dump(config)
    else:
        connect_to_postgres(config)
        execute_postgres_dump(config)

    print('Backup complete!')
