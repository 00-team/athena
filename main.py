
import asyncio

from telebot.async_telebot import AsyncTeleBot

from src.database import check_user_id, setup_database
from src.logger import get_logger
from src.settings import SECRETS

logger = get_logger()

bot = AsyncTeleBot(SECRETS['TOKEN'])
channel_id = SECRETS['CHANNEL_ID']


async def check_user_joined(message):
    member = await bot.get_chat_member(
        chat_id=channel_id,
        user_id=message.from_user.id
    )

    if member.status in ['member', 'creator']:
        return False
    else:
        await bot.reply_to(message, 'please join to channel')
        return True


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    if (await check_user_joined(message)):
        return

    await bot.reply_to(message, 'hi this is test')


@bot.message_handler(
    func=lambda message: True,
    content_types=['photo', 'video', 'text']
)
async def echo_message(message):
    if (await check_user_joined(message)):
        return

    is_forwarded_from_channel = message.forward_from_chat.type

    print(is_forwarded_from_channel)

    if is_forwarded_from_channel == 'channel':
        await bot.forward_message(
            chat_id=channel_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    else:
        await bot.reply_to(message, 'mayel be tamayol?😈🔞')


def main():
    logger.info('Starting Athena')
    setup_database()
    asyncio.run(bot.polling())


if __name__ == '__main__':
    main()
