# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, db, config, _, u, cache
from utils.subscriptions import is_chat_exist
from utils.openai import chatgpt, dalle
from telebot.formatting import escape_markdown
from utils.strings import CallbackData, CacheData

@bot.message_handler(is_chat=True, commands=['start'])
async def start_chat_handler(message):
    """ Чат /start
    """
    await is_chat_exist(message)

@bot.message_handler(is_chat=True, commands=['gpt'])
async def chatgpt_handler(message):
    chat = await db.get_user(message.chat.id, type="chat")

    text = message.text[5::]
    if len(text) < 4:
        await bot.reply_to(
            message,
            _('command_gpt_help')
        )
        return

    await chatgpt.chatgpt(
        chat,
        {
            'message_id': message.message_id,
            'from_user_id': message.from_user.id,
            'chat_id': message.chat.id,
            'text': message.text
        },
        user_type='chat'
    )


@bot.message_handler(is_chat=True, commands=['dalle'])
async def dalle_handler(message):
    chat = await db.get_user(message.chat.id, type="chat")
    text = message.text.replace("/dalle ", "").replace(f"/dalle", "")

    if len(text) < 4:
        await bot.reply_to(
            message,
            _('command_image_help')
        )
        return

    generate_redis_key = CacheData.dalle_generation.format(message.chat.id)
    generate = await cache.get(generate_redis_key)

    if generate is not None:
        await bot.send_message(
            message.chat.id,
            _('waiting_dalle_generation')
        )
        return

    await cache.set(generate_redis_key, 1)
    await dalle.generate_image(chat, message, user_type='chat')
    await cache.delete(generate_redis_key)
