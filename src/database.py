
import json

from .logger import get_logger
from .settings import CHANNEL_DB_PATH, EXPIRE_TIME, USER_DB_PATH
from .tools import now

logger = get_logger('database')

USER_DB = {}
CHANNEL_DB = []


def _save_db(db, path):
    with open(path, 'w') as f:
        json.dump(db, f)


def _setup_db(db, path):
    if not path.exists():
        _save_db(db, path)
        return db

    with open(path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, type(db)):
        raise ValueError('invalid database')

    return data


def setup_databases():
    global USER_DB, CHANNEL_DB

    USER_DB = _setup_db(USER_DB, USER_DB_PATH)
    CHANNEL_DB = _setup_db(CHANNEL_DB, CHANNEL_DB_PATH)


def check_user(user_id):
    user_id = str(user_id)

    if user_id not in USER_DB:
        logger.debug(f'{user_id=} dose not exists in the database')

        USER_DB[user_id] = now() + EXPIRE_TIME
        _save_db(USER_DB, USER_DB_PATH)

        return 0

    expire_date = USER_DB[user_id] - now()

    if expire_date > 0:
        logger.debug(f'{user_id=} exists | {expire_date}s')
        return expire_date

    logger.debug(f'{user_id=} exists and the time is expired')

    USER_DB[user_id] = now() + EXPIRE_TIME
    _save_db(USER_DB, USER_DB_PATH)

    return 0


def channel_add(channel):
    global CHANNEL_DB

    # check if channel exists or not
    for c in CHANNEL_DB:
        if c['id'] == channel['id']:
            return

    CHANNEL_DB.append(channel)
    _save_db(CHANNEL_DB, CHANNEL_DB_PATH)


def channel_remove(channel_id: int):
    global CHANNEL_DB

    for c in CHANNEL_DB:
        if c['id'] == channel_id:
            CHANNEL_DB.remove(c)
            _save_db(CHANNEL_DB, CHANNEL_DB_PATH)
