# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u, loop
from languages.language import lang_variants
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from states.states import AdminDalle
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.configurable import config_update

async def parse_dalle():
    """ Главное меню Dall-e
    """
    service_status = _('dict_service_status')[config.getboolean('service', 'dalle')]

    msg = _('admin_openai_dalle').format(**{
        "mode":  service_status,
        "price": config.get('openai', 'dalle_request_tokens')
    })

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(_('inline_parameters'), callback_data='_')
    ).row(
        InlineKeyboardButton(
            service_status, callback_data=CallbackData.admin_dalle_set_param+'mode'
        ),
    ).row(
        InlineKeyboardButton(_('inline_dalle_param_price'), callback_data=CallbackData.admin_dalle_set_param+'dalle_request_tokens')
    ).row(
        InlineKeyboardButton(
            _('inline_back_to'), callback_data=CallbackData.admin_openai
        )
    )

    return msg, kb

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_dalle, role=['admin', 'demo'])
async def admin_dalle(call):
    """ Главная настроек Dall-E
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_dalle()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_dalle_set_param), role=['admin'])
async def update_chatgpt_settings(call):
    """ Обновляет настройки ChatGPT
    """
    param = call.data.replace(CallbackData.admin_dalle_set_param, '')
    msg, kb = _('service_disabled'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_dalle}
    })

    if not param:
        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )

    if param == 'mode':
        mode = config.get('service', 'dalle')
        new_value = 'False' if mode == 'True' else 'True'
        config.set('service', 'dalle', new_value)
        await config_update()
        msg, kb = await parse_dalle()

    if param in ['dalle_request_tokens']:
        dict_param = _('dict_config_params')[param]
        msg = _('input_new_value_param').format(dict_param)

        await bot.set_state(call.from_user.id, AdminDalle.A1)

        async with bot.retrieve_data(call.from_user.id) as data:
            data['param'] = param

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.message_handler(is_chat=False, state=AdminDalle.A1, role=['admin'])
async def admin_chatgpt_create_dialog(message):
    """ Сохранение настроек Dall-E
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text

        param = data['param']
        dict_param = _('dict_config_params')[param]

        msg = _('param_value_updated').format(dict_param)
        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_dalle}
        })

        if param in ['dalle_request_tokens']:
            try:
                new_val = int(new_val)
            except Exception as e:
                new_val = 0

        config.set('openai', param, str(new_val))

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )

    await bot.delete_state(message.from_user.id)
    await config_update()
