
import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .logger import get_logger
from .settings import CHANNEL_DB_PATH, EXPIRE_TIME, GENERAL_DB_PATH
from .settings import USER_DB_PATH
from .tools import now

logger = get_logger('database')

_USER_DB = {}
_CHANNEL_DB = {}
_GENERAL_DB = {
    'forward_enable': True
}


def save_db(db, path):
    with open(path, 'w') as f:
        json.dump(db, f)


def setup_db(db, path):
    if not path.exists():
        save_db(db, path)
        return db

    with open(path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, type(db)):
        raise ValueError('invalid database')

    return data


def setup_databases():
    global _USER_DB, _CHANNEL_DB, _GENERAL_DB

    _USER_DB = setup_db(_USER_DB, USER_DB_PATH)
    _CHANNEL_DB = setup_db(_CHANNEL_DB, CHANNEL_DB_PATH)
    _GENERAL_DB = setup_db(_GENERAL_DB, GENERAL_DB_PATH)


def get_users():
    return _USER_DB


def get_channels():
    return _CHANNEL_DB


def toggle_forwards():
    _GENERAL_DB['forward_enable'] = not _GENERAL_DB['forward_enable']
    save_db(_GENERAL_DB, GENERAL_DB_PATH)


def is_forwards_enable() -> bool:
    return _GENERAL_DB['forward_enable']


async def get_keyboard_chats(bot):
    fe = '✅' if _GENERAL_DB['forward_enable'] else '❌'
    btns = [[
        InlineKeyboardButton(
            f'forward: {fe}',
            callback_data='toggle_forwards#1'
        )
    ]]

    for cid, cval in get_channels().items():
        cid = int(cid)
        enable = '✅' if cval['enable'] else '❌'
        chat = await bot.get_chat(cid)
        if not chat.invite_link:
            enable = '⚠'

        btns.append([
            InlineKeyboardButton(
                chat.title,
                url=chat.invite_link or 't.me/i007c'
            ),
        ])
        btns.append([
            InlineKeyboardButton(
                f'{cval["amount"]}/{cval["limit"]}',
                callback_data=f'set_chat_limit#{chat.id}'
            ),
            InlineKeyboardButton(
                enable,
                callback_data=f'toggle_chat#{chat.id}'
            ),
            InlineKeyboardButton('⛔', callback_data=f'leave_chat#{chat.id}')
        ])

    return InlineKeyboardMarkup(btns)


def user_add(user):
    user_id = str(user.id)
    if user_id in _USER_DB:
        return

    _USER_DB[user_id] = {
        'expires': 0,
        'username': user.username
    }
    save_db(_USER_DB, USER_DB_PATH)


def check_user(user):
    user_id = str(user.id)

    if user_id not in _USER_DB:
        # logger.debug(f'{user_id=} dose not exists in the database')

        # _USER_DB[user_id] = now() + EXPIRE_TIME
        _USER_DB[user_id] = {
            'expires': now() + EXPIRE_TIME,
            'username': user.username
        }
        save_db(_USER_DB, USER_DB_PATH)

        return 0

    value = _USER_DB[user_id]
    if isinstance(value, int):
        expire_date = value - now()
    else:
        expire_date = value['expires'] - now()

    if expire_date > 0:
        # logger.debug(f'{user_id=} exists | {expire_date}s')
        return expire_date

    # logger.debug(f'{user_id=} exists and the time is expired')

    _USER_DB[user_id] = {
        'expires': now() + EXPIRE_TIME,
        'username': user.username
    }
    save_db(_USER_DB, USER_DB_PATH)

    return 0


def channel_add(cid):
    _CHANNEL_DB[str(cid)] = {
        'enable': False,
        'amount': 0,
        'limit': -1
    }
    save_db(_CHANNEL_DB, CHANNEL_DB_PATH)


def channel_remove(cid):
    global _CHANNEL_DB

    _CHANNEL_DB.pop(str(cid), None)
    save_db(_CHANNEL_DB, CHANNEL_DB_PATH)


def channel_toggle(cid):
    global _CHANNEL_DB

    cid = str(cid)
    if cid not in _CHANNEL_DB:
        return

    _CHANNEL_DB[cid]['enable'] = not _CHANNEL_DB[cid]['enable']
    save_db(_CHANNEL_DB, CHANNEL_DB_PATH)


def channel_add_member(cid):
    global _CHANNEL_DB

    cid = str(cid)
    if cid not in _CHANNEL_DB:
        return

    _CHANNEL_DB[cid]['amount'] += 1
    if (
        _CHANNEL_DB[cid]['limit'] > 1 and
        _CHANNEL_DB[cid]['amount'] >= _CHANNEL_DB[cid]['limit']
    ):
        _CHANNEL_DB[cid]['enable'] = False

    save_db(_CHANNEL_DB, CHANNEL_DB_PATH)


def channel_set_limit(cid, limit):
    cid = str(cid)
    if cid not in _CHANNEL_DB:
        return

    _CHANNEL_DB[cid]['limit'] = limit
    save_db(_CHANNEL_DB, CHANNEL_DB_PATH)
