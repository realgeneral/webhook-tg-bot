# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u
from languages.language import lang_variants
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from states.states import AdminChatGpt
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

async def parse_home_openai():
    """ Главное меню OpenAi
    """
    msg = _('admin_select_openai_service')
    kb = BotKeyboard.smart({
        _('inline_admin_chatgpt'): {'callback_data': CallbackData.admin_chatgpt},
        # _('inline_admin_gpt_models'): {'callback_data': CallbackData.admin_models},
        _('inline_admin_dalle'): {'callback_data': CallbackData.admin_dalle},
        _('inline_back_to'): {'callback_data': CallbackData.admin_home},
    })

    return msg, kb

@bot.callback_query_handler(func=lambda call: call.data == CallbackData.admin_openai)
async def admin_home_openai(call):
    """ Главная настроек OpenAi
    """
    msg, kb = await parse_home_openai()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(func=lambda call: call.data == CallbackData.admin_models)
async def admin_home_openai(call):
    """ Модели ChatGPT
    """
    models = config.get('openai', 'models').split('\n')
    kb = {
        i: {'callback_data': 'te'}
        for i in models
    }
    kb.update({
        _('inline_back_to'): {'callback_data': CallbackData.admin_openai}
    })
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('chatgpt_models'),
        reply_markup = BotKeyboard.smart(kb)
    )
