
import json

from src.logger import get_logger
from src.settings import BASE_DIR
from src.tools import now

logger = get_logger()


DATABASE_PATH = BASE_DIR / 'data/database.json'
DATABASE = {}
# EXPIRE_TIME = 6 * 60 * 60
EXPIRE_TIME = 7


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


# run this after each database change
def save_database():
    with open(DATABASE_PATH, 'w') as f:
        json.dump(DATABASE, f)


def check_user_id(user_id):
    if user_id not in DATABASE:
        logger.info(f'{user_id=} dose not exists in the database')
        DATABASE[user_id] = now() + EXPIRE_TIME
        save_database()
        return

    expire_date = DATABASE[user_id]
    dt = now()

    if expire_date > dt:
        logger.info(f'{user_id=} exists | {expire_date-dt}s')
        return

    logger.info(f'{user_id=} exists and the time is expired')
    DATABASE[user_id] = now() + EXPIRE_TIME
    save_database()


def main():
    logger.info('Starting Athena')
    setup_database()

    while True:
        user_id = input('Enter User ID > ')
        check_user_id(user_id)


if __name__ == '__main__':
    main()
