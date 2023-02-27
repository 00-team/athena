
import json

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from .logger import get_logger
from .settings import CHANNEL_DB_PATH, EXPIRE_TIME, USER_DB_PATH
from .tools import now

logger = get_logger('database')

_USER_DB = {}
_CHANNEL_DB = []


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
    global _USER_DB, _CHANNEL_DB

    _USER_DB = _setup_db(_USER_DB, USER_DB_PATH)
    _CHANNEL_DB = _setup_db(_CHANNEL_DB, CHANNEL_DB_PATH)


def get_users():
    return _USER_DB


def get_channels():
    return _CHANNEL_DB


async def get_keyboard_chats(bot):
    chats = []
    for c in _CHANNEL_DB:
        enable = '✅' if c['enable'] else '❌'
        chat = await bot.get_chat(c['id'])

        chats.append([
            InlineKeyboardButton(chat.title, url=chat.invite_link),
            InlineKeyboardButton(
                enable,
                callback_data=f'toggle-chat-{chat.id}'
            ),
        ])

    return InlineKeyboardMarkup(chats)


def check_user(user_id):
    user_id = str(user_id)

    if user_id not in _USER_DB:
        logger.debug(f'{user_id=} dose not exists in the database')

        _USER_DB[user_id] = now() + EXPIRE_TIME
        _save_db(_USER_DB, USER_DB_PATH)

        return 0

    expire_date = _USER_DB[user_id] - now()

    if expire_date > 0:
        logger.debug(f'{user_id=} exists | {expire_date}s')
        return expire_date

    logger.debug(f'{user_id=} exists and the time is expired')

    _USER_DB[user_id] = now() + EXPIRE_TIME
    _save_db(_USER_DB, USER_DB_PATH)

    return 0


def channel_add(channel):
    global _CHANNEL_DB

    # check if channel exists or not
    for c in _CHANNEL_DB:
        if c['id'] == channel['id']:
            return

    _CHANNEL_DB.append(channel)
    _save_db(_CHANNEL_DB, CHANNEL_DB_PATH)


def channel_remove(channel_id: int):
    global _CHANNEL_DB

    for c in _CHANNEL_DB:
        if c['id'] == channel_id:
            _CHANNEL_DB.remove(c)
            _save_db(_CHANNEL_DB, CHANNEL_DB_PATH)


def channel_toggle(channel_id: int):
    global _CHANNEL_DB

    for idx, c in enumerate(_CHANNEL_DB):
        if c['id'] == channel_id:
            c['enable'] = not c['enable']
            _CHANNEL_DB[idx] = c
            _save_db(_CHANNEL_DB, CHANNEL_DB_PATH)
            break
