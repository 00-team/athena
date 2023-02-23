from telebot.async_telebot import AsyncTeleBot
import json


bot = AsyncTeleBot('1918298985:AAFCpS_4svAB5UbneTiMZ-ooumJsN5Cl-x0')

channel_id = "@afjdkdjsklska09312"



async def check_user_joined(message):
    is_member = (await bot.get_chat_member(chat_id=channel_id, user_id=message.from_user.id)).status
    if is_member in ['member', 'creator']:
        return False
    else:
        await bot.reply_to(message, 'please join to channel')
        return True


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    if (await check_user_joined(message)):
        return
    await bot.reply_to(message, "hi this is test")




@bot.message_handler(func=lambda message: True, content_types=['photo', 'video', 'text'])
async def echo_message(message):
    if (await check_user_joined(message)):
        return
    is_forwarded_from_channel = message.forward_from_chat.type
    print(is_forwarded_from_channel)
    if is_forwarded_from_channel == "channel":
        await bot.forward_message(chat_id=channel_id, from_chat_id=message.chat.id, message_id=message.message_id)
    else:
        await bot.reply_to(message, "mayel be tamayol?😈🔞")



import asyncio
asyncio.run(bot.polling())