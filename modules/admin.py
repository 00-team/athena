
import html
import json
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import NetworkError
from telegram.ext import ContextTypes

from shared.database import get_users
from shared.dependencies import require_admin
from shared.logger import get_logger
from shared.settings import SECRETS

logger = get_logger('admin')


@require_admin
async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text((
        '/usernames -> get all the usernames\n'
        '/start -> get list of channels\n'
        '/send_all -> send a message to all users\n'
        '/help -> for getting the message\n'
        '🐧'
    ))


@require_admin
async def get_all_usernames(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    msg = update.message
    users = get_users().items()
    await msg.reply_text(f'user count: {len(users)} 🐧')

    size = 0
    text = ''

    for uid, val in users:
        if isinstance(val, int) or not val['username']:
            continue

        username = val['username']
        add_size = len(username) + 2

        if size + add_size > 1000:
            await msg.reply_text(text)
            text = f'@{username} '
            size = add_size
        else:
            text += f'@{username} '
            size += add_size

    await msg.reply_text(text)


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    if isinstance(ctx.error, NetworkError):
        logger.error('a network error has occurred.')
        return

    logger.error(
        msg='Exception while handling an update:',
        exc_info=ctx.error
    )

    tb_list = traceback.format_exception(
        None, ctx.error, ctx.error.__traceback__
    )
    tb_string = ''.join(tb_list)

    if isinstance(update, Update):
        update_str = json.dumps(update.to_dict(), indent=2, ensure_ascii=False)
    else:
        update_str = str(update)

    message = (
        f'An exception was raised while handling an update\n\n'
        f'<pre>{html.escape(update_str)}</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(ctx.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(ctx.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )
    logger.debug('dev: ' + str(SECRETS['DEVELOPER']))

    await ctx.bot.send_message(
        chat_id=SECRETS['DEVELOPER'], text=message, parse_mode=ParseMode.HTML
    )
