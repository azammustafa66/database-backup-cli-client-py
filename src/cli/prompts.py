import questionary


def prompt_db_type() -> str:
    return questionary.select(
        'Select the database engine:',
        choices=[
            questionary.Choice(title='MongoDB', value='mongodb'),
            questionary.Choice(title='PostgreSQL', value='postgres'),
        ],
    ).unsafe_ask()


# Mutates `config` in place so the caller accumulates all gathered values.
def prompt_mongo_credentials(config: dict) -> None:
    use_uri = questionary.select(
        'How would you like to connect?',
        choices=[
            questionary.Choice(
                title='Connection String (URI) - Recommended for Atlas', value='uri'
            ),
            questionary.Choice(title='Manual Host & Port - Recommended for Local', value='manual'),
        ],
    ).unsafe_ask()

    if use_uri == 'uri':
        config['uri'] = questionary.password('Paste your MongoDB URI (input hidden):').unsafe_ask()
    else:
        config['host'] = questionary.text('Database Host:', default='localhost').unsafe_ask()
        config['port'] = questionary.text('Database Port:', default='27017').unsafe_ask()
        config['user'] = questionary.text('Database Username (leave blank if none):').unsafe_ask()
        config['password'] = questionary.password(
            'Database Password (leave blank if none):'
        ).unsafe_ask()


def prompt_postgres_credentials(config: dict) -> None:
    config['host'] = questionary.text('Database Host:', default='localhost').unsafe_ask()
    config['port'] = questionary.text('Database Port:', default='5432').unsafe_ask()
    config['user'] = questionary.text('Database Username:', default='postgres').unsafe_ask()
    config['database_name'] = questionary.text('Database Name:', default='postgres').unsafe_ask()
    config['password'] = questionary.password(
        'Database Password (leave blank if none):'
    ).unsafe_ask()
