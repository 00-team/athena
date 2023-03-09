

import html
import json
import traceback
from time import sleep

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import Forbidden, RetryAfter, TelegramError
from telegram.ext import Application, CallbackQueryHandler, ChatMemberHandler
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from modules.admin import get_all_usernames, help_command
from modules.chat import chat_member_update
from shared.database import channel_add, channel_remove, channel_toggle
from shared.database import check_user, get_keyboard_chats, get_users
from shared.database import is_forwards_enable, setup_databases
from shared.database import toggle_forwards
from shared.dependencies import require_admin, require_joined
from shared.logger import get_logger
from shared.settings import FORWARD_DELAY, SECRETS

logger = get_logger()


MAIN_CHANNEL = SECRETS['CHANNEL']
FORWARD_ALL = {}


@require_joined
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if user.id in SECRETS['ADMINS']:
        await update.message.reply_text(
            'list of all channels',
            reply_markup=await get_keyboard_chats(ctx.bot)
        )
    else:
        await update.message.reply_text(
            'خوش آمدید، برای ارسال بنر در کانال بنر خود را فوروارد کنید.',
        )


@require_admin
async def send_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    FORWARD_ALL[user.id] = not FORWARD_ALL.get(user.id, False)

    await update.message.reply_text(
        f'ok. forward your message: {FORWARD_ALL[user.id]}'
    )


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(
        msg='Exception while handling an update:',
        exc_info=ctx.error
    )
    logger.debug(f'{isinstance(ctx.error, TelegramError)=}')

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

    await ctx.bot.send_message(
        chat_id=SECRETS['DEVELOPER'], text=message, parse_mode=ParseMode.HTML
    )


async def send_all_job(ctx: ContextTypes.DEFAULT_TYPE):
    for uid in get_users().keys():
        sleep(5)
        uid = int(uid)
        try:
            chat = await ctx.bot.get_chat(uid)
            if chat.type != 'private':
                return

            await ctx.bot.forward_message(
                uid,
                from_chat_id=ctx.job.chat_id,
                message_id=ctx.job.data,
            )
        except RetryAfter as e:
            sleep(e.retry_after + 10)
        except Forbidden:
            pass
        except TelegramError as e:
            logger.exception(e)


async def forward_to_channel_job(ctx: ContextTypes.DEFAULT_TYPE):
    await ctx.bot.forward_message(
        MAIN_CHANNEL,
        from_chat_id=ctx.job.chat_id,
        message_id=ctx.job.data,
    )


@require_joined
async def send_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = msg.from_user

    if (
        not msg.forward_from_chat or
        msg.forward_from_chat.type != 'channel'
    ):
        return

    if FORWARD_ALL.pop(user.id, False):
        ctx.job_queue.run_once(
            send_all_job, 1,
            chat_id=msg.chat.id,
            user_id=user.id,
            data=msg.message_id,
            name='send_all'
        )
        await msg.reply_text('running... 🐧')
        return

    if not is_forwards_enable():
        await msg.reply_text(
            ('فعلا ربات خاموشه وقتی اومدم فور میزنم تا اون موقع میتونی از'
             ' گروه جفج دیدن کنی @joinforjoindaily')
        )
        return

    exp = check_user(user)

    h = exp // 3600
    m = exp % 3600 // 60
    s = exp % 3600 % 60

    if exp:
        await msg.reply_text(
            (f'شما به تازگی پیام ارسال کردید برای ارسال'
             f' مجدد پیام باید {h}:{m}:{s} صبر کنید.')
        )
        return

    ctx.job_queue.run_once(
        forward_to_channel_job, FORWARD_DELAY,
        chat_id=msg.chat.id,
        user_id=user.id,
        data=msg.message_id,
    )

    await msg.reply_text((
        'پست شما با موفقیت برای ادمین ارسال شد در صورت تایید'
        ' ،در چنل گذاشته میشود.\n\n'
        'مطمعن شوید پست زیر رو به چنلتون فور زدید\n'
        'https://t.me/daily_gostardeh/95'
    ))

    # await msg.forward(MAIN_CHANNEL)


async def my_chat_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    e = update.my_chat_member

    if e.chat.type not in ['channel', 'supergroup']:
        # await ctx.bot.leave_chat(e.chat.id)
        return

    if e.new_chat_member.status == 'administrator':
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
        await ctx.bot.leave_chat(e.chat.id)


async def query_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data or not query.message:
        return

    data = query.data.split('#')

    if len(data) != 2:
        return

    action, cid = data
    cid = int(cid)

    if action == 'toggle_chat':
        channel_toggle(cid)
    elif action == 'leave_chat':
        if (await ctx.bot.leave_chat(cid)):
            channel_remove(cid)
    elif action == 'toggle_forwards':
        toggle_forwards()
    else:
        return

    await query.edit_message_reply_markup(await get_keyboard_chats(ctx.bot))


def main():
    logger.info('Starting Athena')
    setup_databases()

    application = Application.builder().token(SECRETS['TOKEN']).build()
    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('usernames', get_all_usernames))
    application.add_handler(CommandHandler('send_all', send_all))

    application.add_handler(ChatMemberHandler(
        my_chat_update, ChatMemberHandler.MY_CHAT_MEMBER
    ))
    application.add_handler(ChatMemberHandler(
        chat_member_update, ChatMemberHandler.CHAT_MEMBER
    ))
    application.add_handler(CallbackQueryHandler(query_update))
    application.add_handler(MessageHandler(
        ((filters.TEXT | filters.PHOTO) &
         (filters.FORWARDED & filters.ChatType.PRIVATE)),
        send_message
    ))

    application.run_polling()


if __name__ == '__main__':
    main()
