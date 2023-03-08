
from telegram import Update
from telegram.ext import ContextTypes

from shared.database import get_users
from shared.dependencies import require_admin


@require_admin
async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text((
        '/usernames -> get all the usernames\n'
        '/start -> get list of channels\n'
        '/send_all -> send a message to all users\n'
        '🐧'
    ))


@require_admin
async def get_all_usernames(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    users = get_users().items()
    text = f'user count: {len(users)}\n'

    for uid, val in users:
        if isinstance(val, int) or not val['username']:
            continue

        text += f"@{val['username']} "

    await update.message.reply_text(text)
