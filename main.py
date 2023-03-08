

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, CallbackQueryHandler, ChatMemberHandler
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from modules.admin import get_all_usernames, help_command
from shared.database import channel_add, channel_remove, channel_toggle
from shared.database import check_user, get_keyboard_chats, get_users
from shared.database import is_forwards_enable, setup_databases
from shared.database import toggle_forwards
from shared.dependencies import require_admin, require_joined
from shared.logger import get_logger
from shared.settings import SECRETS

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
async def forward_to_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    FORWARD_ALL[user.id] = not FORWARD_ALL.get(user.id, False)

    await update.message.reply_text(
        f'ok. forward your message: {FORWARD_ALL[user,id]}'
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
        for uid in get_users().keys():
            try:
                await msg.forward(int(uid))
            except TelegramError as e:
                logger.exception(e)

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

    await msg.forward(MAIN_CHANNEL)


async def my_chat_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    e = update.my_chat_member

    if e.chat.type not in ['channel', 'supergroup']:
        await ctx.bot.leave_chat(e.chat.id)
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

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('usernames', get_all_usernames))
    application.add_handler(CommandHandler('ftoall', forward_to_all))

    application.add_handler(ChatMemberHandler(
        my_chat_update, ChatMemberHandler.MY_CHAT_MEMBER
    ))
    application.add_handler(CallbackQueryHandler(query_update))
    application.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO) & filters.FORWARDED,
        send_message
    ))

    application.run_polling()


if __name__ == '__main__':
    main()
