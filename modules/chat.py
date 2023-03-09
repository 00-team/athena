
from telegram import Update
from telegram.ext import ContextTypes

from shared.logger import get_logger

logger = get_logger(__package__)


async def chat_member_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.info('chat member update ...')
    name = update.chat_member.chat.title
    user = update.chat_member.from_user.first_name

    logger.info(f'chat {name}: {user}')
