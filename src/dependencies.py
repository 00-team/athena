
from telebot.asyncio_helper import ApiTelegramException
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from .database import channel_remove, get_channels
from .logger import get_logger
from .settings import SECRETS, bot

logger = get_logger('dependencies')


def require_admin(func):
    async def decorator(update):
        if update.from_user.id in SECRETS['ADMINS']:
            return await func(update)

    return decorator


def require_joined(func):
    async def decorator(message):
        not_joined = []
        user_id = message.from_user.id

        if user_id in SECRETS['ADMINS']:
            await func(message)
            return

        for channel in get_channels():
            if not channel['enable']:
                continue

            chat_id = channel['id']
            try:
                member = await bot.get_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                )
                if member.status in ['left', 'kicked']:
                    chat = await bot.get_chat(chat_id)
                    if not chat.invite_link:
                        continue
                    not_joined.append(
                        [InlineKeyboardButton(
                            chat.title, url=chat.invite_link)]
                    )

            except ApiTelegramException as e:
                logger.exception(e)
                channel_remove(chat_id)
                continue

        if not_joined:
            await bot.send_message(
                user_id,
                'اول مطمئن شوید که در کانال های زیر عضو شدید.',
                reply_markup=InlineKeyboardMarkup(not_joined)
            )

        else:
            await func(message)

    return decorator


__all__ = [
    'require_admin',
    'require_joined',
]
