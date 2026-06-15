import os
import sys

import questionary

from src.commands.backup import handle_backup_flow
from src.commands.restore import handle_restore_flow


def main() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    print('--------------------------------------------')
    print('  Welcome to the DB Backup and Restore CLI  ')
    print('--------------------------------------------\n')

    try:
        action = questionary.select(
            'What would you like to do?',
            choices=[
                questionary.Choice(title='Backup a Database', value='backup'),
                questionary.Choice(title='Restore a Database', value='restore'),
                questionary.Choice(title='Exit', value='exit'),
            ],
        ).unsafe_ask()

        if action == 'exit':
            print('Goodbye!')
            sys.exit(0)

        if action == 'backup':
            handle_backup_flow()
        elif action == 'restore':
            handle_restore_flow()
    except KeyboardInterrupt:
        print('\nWizard cancelled. Goodbye!')
    except Exception as error:
        print(f'\nAn unexpected error occurred: {error}')


if __name__ == '__main__':
    main()
