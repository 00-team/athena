
import asyncio

from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.database import channel_add, channel_remove, channel_toggle
from src.database import check_user, get_channels, get_keyboard_chats
from src.database import get_users, is_forwards_enable, setup_databases
from src.database import toggle_forwards
from src.logger import get_logger
from src.settings import SECRETS

logger = get_logger()

bot = AsyncTeleBot(SECRETS['TOKEN'])
MAIN_CHANNEL = SECRETS['CHANNEL']


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
                    not_joined.append(
                        [InlineKeyboardButton(
                            chat.title, url=chat.invite_link)]
                    )

            except Exception as e:
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


def check_forwarded(m):
    return m and m.forward_from_chat and m.forward_from_chat.type == 'channel'


@bot.message_handler(
    func=check_forwarded,
    content_types=['text', 'photo']
)
@require_joined
async def send_message(message):
    if not is_forwards_enable():
        await bot.reply_to(
            message,
            ('فعلا ربات خاموشه وقتی اومدم فور میزنم تا اون موقع میتونی از'
             ' گروه جفج دیدن کنی @joinforjoindayli')
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


@bot.message_handler(commands=['f'])
async def forward_to_all(message):
    user_id = message.from_user.id
    if user_id not in SECRETS["ADMINS"]:
        return

    text = ''
    for uid, val in get_users().items():
        if isinstance(val, int) or not val['username']:
            continue

        text += f"@{val['username']} - "

    await bot.send_message(user_id, text)


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
