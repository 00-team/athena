
import json

from src.logger import get_logger
from src.settings import BASE_DIR

logger = get_logger()


DATABASE_PATH = BASE_DIR / 'data/database.json'
DATABASE = {}


def setup_database():
    global DATABASE

    if not DATABASE_PATH.exists():
        # create the data directory
        DATABASE_PATH.parent.mkdir(exist_ok=True)

        # init the file
        with open(DATABASE_PATH, 'w') as f:
            f.write('{}\n')

        return

    # so if there is a database then read the data
    with open(DATABASE_PATH, 'r') as f:
        DATABASE = json.load(f)

    # check if database is valid or not
    if not isinstance(DATABASE, dict):
        raise ValueError('invalid database')


def check_user_id(user_id):
    pass


def main():
    logger.info('Starting Athena')
    setup_database()

    while True:
        user_id = input('Enter User ID > ')
        check_user_id(user_id)


if __name__ == '__main__':
    main()
