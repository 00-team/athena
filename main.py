
import asyncio

from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.database import CHANNEL_DB, channel_add, channel_remove, check_user
from src.database import setup_databases
from src.logger import get_logger
from src.settings import SECRETS

logger = get_logger()

bot = AsyncTeleBot(SECRETS['TOKEN'])
MAIN_CHANNEL = SECRETS['CHANNEL']


def require_joined(func):
    async def decorator(message):
        not_joined = []
        user_id = message.from_user.id

        for channel in CHANNEL_DB:
            if not channel['enable']:
                continue

            chat_id = channel['id']
            member = await bot.get_chat_member(
                chat_id=chat_id,
                user_id=user_id,
            )

            if member.status in ['left', 'kicked']:
                chat = await bot.get_chat(chat_id)
                not_joined.append(
                    [InlineKeyboardButton(chat.title, url=chat.invite_link)]
                )

        if not_joined:
            await bot.send_message(
                user_id,
                'join this channels first',
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
        chats = []
        for c in CHANNEL_DB:
            enable = '✅' if c['enable'] else '❌'
            chat = await bot.get_chat(c['id'])

            chats.append([
                InlineKeyboardButton(chat.title, url=chat.invite_link),
                InlineKeyboardButton(
                    enable,
                    callback_data=f'toggle-chat-{chat.id}'
                ),
            ])

        await bot.reply_to(
            message,
            reply_markup=InlineKeyboardMarkup(chats)
        )

    else:
        await bot.reply_to(message, 'hi this is test')


def check_forwarded(m):
    return m and m.forward_from_chat and m.forward_from_chat.type == 'channel'


@bot.message_handler(
    func=check_forwarded,
    content_types=['text']
)
@require_joined
async def send_message(message):
    exp = check_user(message.from_user.id)
    if exp:
        bot.reply_to(message, f'you already send a message. wait about {exp}s')
        return

    await bot.forward_message(
        chat_id=MAIN_CHANNEL,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )


@bot.my_chat_member_handler()
async def chat_update(update):
    # if update.from_user.id not in SECRETS['ADMINS']:
    #     await bot.leave_chat(update.chat.id)
    #     return

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


def main():
    logger.info('Starting Athena')
    setup_databases()
    asyncio.run(bot.polling())


if __name__ == '__main__':
    main()
