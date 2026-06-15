import os
import sys

import questionary

from src.cli.prompts import (prompt_db_type, prompt_mongo_credentials,
                             prompt_postgres_credentials)
from src.db.mongo import execute_mongo_restore
from src.db.postgres import execute_postgres_restore


def handle_restore_flow() -> None:
    db_type = prompt_db_type()
    config = {'type': db_type}

    config['out'] = questionary.text(
        'Where is the backup stored?',
        default='./backups',
    ).unsafe_ask()

    if db_type == 'mongodb':
        prompt_mongo_credentials(config)
    else:
        prompt_postgres_credentials(config)

    print('\n=========================================')
    print('Initiating Restore Process...')
    print('=========================================\n')

    if not os.path.exists(config['out']):
        print('Backup folder does not exist.')
        sys.exit(1)

    if db_type == 'mongodb':
        execute_mongo_restore(config)
    else:
        execute_postgres_restore(config)

    print('Restore complete!')
