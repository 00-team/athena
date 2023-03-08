
import asyncio

from telebot.asyncio_helper import ApiTelegramException

from src.database import channel_add, channel_remove, channel_toggle
from src.database import check_user, get_keyboard_chats, get_users
from src.database import is_forwards_enable, setup_databases, toggle_forwards
from src.dependencies import require_admin, require_joined
from src.logger import get_logger
from src.settings import SECRETS, bot

logger = get_logger()


MAIN_CHANNEL = SECRETS['CHANNEL']
FORWARD_ALL = {}


@bot.message_handler(commands=['start'])
@require_joined
async def start(message):
    user_id = message.from_user.id
    if user_id in SECRETS['ADMINS']:
        await bot.reply_to(
            message,
            'list of all channels',
            reply_markup=await get_keyboard_chats(bot)
        )
    else:
        await bot.reply_to(
            message,
            'خوش آمدید، برای ارسال بنر در کانال بنر خود را فوروارد کنید.'
        )


@bot.message_handler(
    func=(
        lambda m: m.forward_from_chat and m.forward_from_chat.type == 'channel'
    ),
    content_types=['text', 'photo']
)
@require_joined
async def send_message(message):
    user_id = message.from_user.id

    if FORWARD_ALL.pop(user_id, False):
        for uid in get_users().keys():
            try:
                await bot.forward_message(
                    chat_id=int(uid),
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )
            except ApiTelegramException as e:
                logger.exception(e)

        return

    if not is_forwards_enable():
        await bot.reply_to(
            message,
            ('فعلا ربات خاموشه وقتی اومدم فور میزنم تا اون موقع میتونی از'
             ' گروه جفج دیدن کنی @joinforjoindaily')
        )
        return

    exp = check_user(message.from_user)

    h = exp // 3600
    m = exp % 3600 // 60
    s = exp % 3600 % 60

    if exp:
        await bot.reply_to(
            message,
            (f'شما به تازگی پیام ارسال کردید برای ارسال'
             f' مجدد پیام باید {h}:{m}:{s} صبر کنید.')
        )
        return

    await bot.forward_message(
        chat_id=MAIN_CHANNEL,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )


@bot.message_handler(commands=['usernames'])
@require_admin
async def get_all_usernames(message):
    user_id = message.from_user.id

    users = get_users().items()
    text = f'user count: {len(users)}\n'

    for uid, val in users:
        if isinstance(val, int) or not val['username']:
            continue

        text += f"@{val['username']} "

    await bot.send_message(user_id, text)


@bot.message_handler(commands=['ftoall'])
@require_admin
async def forward_to_all(message):
    user_id = message.from_user.id

    FORWARD_ALL[user_id] = not FORWARD_ALL.get(user_id, False)
    await bot.reply_to(
        message, f'ok. forward your message: {FORWARD_ALL[user_id]}'
    )


@bot.message_handler(commands=['test'])
@require_admin
async def test_cmd(message):
    await bot.reply_to(message, 'TEST COMMAND')


@bot.my_chat_member_handler()
async def chat_update(update):
    if update.chat.type not in ['channel', 'supergroup']:
        await bot.leave_chat(update.chat.id)
        return

    if update.new_chat_member.status == 'administrator':
        channel_add({
            'id': update.chat.id,
            'enable': False
        })

        await bot.send_message(
            update.from_user.id,
            f'channel {update.chat.title} was added'
        )

    else:
        channel_remove(update.chat.id)
        await bot.leave_chat(update.chat.id)


def check_query(u):
    if not u.data or not u.message:
        return False

    res = u.data.split('#')

    if len(res) != 2:
        return False

    if res[0] not in ['leave_chat', 'toggle_chat', 'toggle_forwards']:
        return False

    return True


@bot.callback_query_handler(func=check_query)
async def query_update(update):
    action, cid = update.data.split('#')
    cid = int(cid)

    if action == 'toggle_chat':
        channel_toggle(cid)

    elif action == 'leave_chat':
        if (await bot.leave_chat(cid)):
            channel_remove(cid)

    elif action == 'toggle_forwards':
        toggle_forwards()

    await bot.edit_message_reply_markup(
        update.from_user.id,
        update.message.id,
        reply_markup=await get_keyboard_chats(bot)
    )


def main():
    logger.info('Starting Athena')
    setup_databases()
    asyncio.run(bot.polling())


if __name__ == '__main__':
    main()
