# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, _
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

async def admin_parse(message):
    """Хоумпейдж админки"""
    main_config = await db.get_config()
    count_users = await db.get_count("users")
    count_chats = await db.get_count("users", q={"type": "chat"})
    msg = _(
        message.from_user.language_code,
        'admin_start_text'
    ).format(
        count_users,
        count_chats,
        main_config['mode'],
        main_config['request_limit_chatgpt'],
        main_config['request_limit_dalle']
    )
    # === MOVE TO keyboards.py === #
    admin_start_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⚙️ Переключить режим ({main_config['mode']})", callback_data='admin.change_mode')],
        [InlineKeyboardButton('💬 Изменить лимит для ChatGPT', callback_data='admin.change_request_limit_chatgpt')],
        [InlineKeyboardButton('🌅 Изменить лимит для Dall-E', callback_data='admin.change_request_limit_dalle')],
        [InlineKeyboardButton('👤 Выдать/забрать подписку', callback_data='admin.view_user')],
        [InlineKeyboardButton("📮 Создать рассылку", callback_data='admin.create_newsletter')],
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='bot.back')],
    ])
    return msg, admin_start_keyboard
