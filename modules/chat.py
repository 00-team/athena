
import json

from telegram import Update
from telegram.ext import ContextTypes

from shared.database import channel_add, channel_remove
from shared.logger import get_logger

logger = get_logger(__package__)


async def chat_member_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.info('chat member update ...')
    logger.debug(json.dumps(update.to_dict(), indent=2))

    name = update.chat_member.chat.title
    user = update.chat_member.from_user.first_name

    logger.info(f'chat {name}: {user}')


async def my_chat_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.debug(json.dumps(update.to_dict(), indent=2))

    e = update.my_chat_member
    status = e.new_chat_member.status

    if e.chat.type not in ['channel', 'supergroup']:
        # await ctx.bot.leave_chat(e.chat.id)
        return

    if status == 'administrator':
        channel_add({
            'id': e.chat.id,
            'enable': False
        })

        await ctx.bot.send_message(
            e.from_user.id,
            f'channel {e.chat.title} was added'
        )

    else:
        channel_remove(e.chat.id)
        if status not in ['left', 'kicked']:
            await ctx.bot.leave_chat(e.chat.id)
