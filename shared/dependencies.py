
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import NetworkError, TelegramError
from telegram.ext import ContextTypes

from .database import get_channels, user_add
from .logger import get_logger
from .settings import SECRETS

logger = get_logger('dependencies')


def require_admin(func):
    async def decorator(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.from_user:
            return

        user = update.message.from_user
        if user.id in SECRETS['ADMINS']:
            return await func(update, ctx)

    return decorator


def require_joined(func):
    async def decorator(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.from_user:
            return

        not_joined = []
        user = update.message.from_user
        user_add(user)

        if user.id in SECRETS['ADMINS']:
            await func(update, ctx)
            return

        for cid, cval in get_channels().items():
            cid = int(cid)
            if not cval['enable']:
                continue

            try:
                member = await ctx.bot.get_chat_member(cid, user.id)

                if member.status in ['left', 'kicked']:
                    chat = await ctx.bot.get_chat(cid)
                    if not chat.invite_link:
                        continue
                    not_joined.append([
                        InlineKeyboardButton(
                            chat.title, url=chat.invite_link
                        )
                    ])

            except NetworkError:
                continue
            except TelegramError as e:
                logger.exception(e)
                # channel_remove(chat_id)
                continue

        if not_joined:
            await update.message.reply_text(
                'اول مطمئن شوید که در کانال های زیر عضو شدید.',
                reply_markup=InlineKeyboardMarkup(not_joined)
            )

        else:
            await func(update, ctx)

    return decorator


__all__ = [
    'require_admin',
    'require_joined',
]
