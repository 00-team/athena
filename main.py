
import asyncio

from telebot.async_telebot import AsyncTeleBot

from src.database import CHANNEL_DB, check_user, setup_databases
from src.logger import get_logger
from src.settings import SECRETS

logger = get_logger()

bot = AsyncTeleBot(SECRETS['TOKEN'])
MAIN_CHANNEL = SECRETS['CHANNEL']


def require_joined(func):
    async def decorator(message):
        for channel_id in CHANNEL_DB:
            member = await bot.get_chat_member(
                chat_id=channel_id,
                user_id=message.from_user.id
            )

            if member.status in ['left', 'kicked']:
                await bot.reply_to(message, f'join to {channel_id} first')
                break

        else:
            await func(message)
    return decorator
            


@bot.message_handler(commands=['start'])
@require_joined
async def start(message):
    await bot.reply_to(message, 'hi this is test')


def check_forwarded(m):
    return m and m.forward_from_chat and m.forward_from_chat.type == 'channel'


@bot.message_handler(
    func=check_forwarded,
    content_types=['photo', 'video', 'text']
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
    if update.from_user.id != 224575002:
        return
    if update.chat.type not in ['channel','supergroup']:
        return
    if update.new_chat_member.status != "kicked":
        return
    



def main():
    logger.info('Starting Athena')
    setup_databases()
    asyncio.run(bot.polling())


if __name__ == '__main__':
    main()
