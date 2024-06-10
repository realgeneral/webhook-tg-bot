# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u, loop
from languages.language import lang_variants
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from states.states import AdminAffiliate
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.configurable import config_update

async def parse_affiliate():
    """ Главное меню рефералки
    """
    service_status = _('dict_service_status')[config.getboolean('default', 'affiliate')]

    msg = _('admin_affiliate').format(**{
        "mode": service_status,
        "affiliate_tokens": config.get('default', 'affiliate_tokens'),
        "affiliate_payment_percent": config.get('default', 'affiliate_payment_percent'),
    })

    kb = InlineKeyboardMarkup()

    kb.row(
        InlineKeyboardButton(
            service_status, callback_data=CallbackData.admin_affiliate_set_param+'mode'
        )
    ).row(
        InlineKeyboardButton(
            _('inline_affiliate_param_at'),
            callback_data=CallbackData.admin_affiliate_set_param+'affiliate_tokens'
        )
    ).row(
        InlineKeyboardButton(
            _('inline_affiliate_param_ap'),
            callback_data=CallbackData.admin_affiliate_set_param+'affiliate_payment_percent'
        )
    ).row(
        InlineKeyboardButton(
            _('inline_back_to'), callback_data=CallbackData.admin_home
        )
    )

    return msg, kb

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_affiliate, role=['admin', 'demo'])
async def admin_chatgpt(call):
    """ Главная настроек ChatGPT
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_affiliate()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_affiliate_set_param), role=['admin'])
async def update_ref_settings(call):
    """ Обновляет настройки рефки
    """
    param = call.data.replace(CallbackData.admin_affiliate_set_param, '')
    msg, kb = _('service_disabled'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_affiliate}
    })

    if not param:
        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )

    if param == 'mode':
        mode = config.get('default', 'affiliate')
        new_value = 'False' if mode == 'True' else 'True'
        config.set('default', 'affiliate', new_value)
        await config_update()
        msg, kb = await parse_affiliate()

    if param in ['affiliate_tokens', 'affiliate_payment_percent']:
        dict_param = _('dict_config_params')[param]
        msg = _('input_new_value_param').format(dict_param)

        await bot.set_state(call.from_user.id, AdminAffiliate.B1)

        async with bot.retrieve_data(call.from_user.id) as data:
            data['param'] = param

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.message_handler(is_chat=False, state=AdminAffiliate.B1, role=['admin'])
async def admin_chatgpt_create_dialog(message):
    """ Сохранение настроек рефки
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text

        param = data['param']
        dict_param = _('dict_config_params')[param]

        msg = _('param_value_updated').format(dict_param)
        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_affiliate}
        })

        if param in ['affiliate_tokens', 'affiliate_payment_percent']:
            try:
                new_val = int(new_val)
            except Exception as e:
                new_val = 0

        config.set('default', param, str(new_val))

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )

    await bot.delete_state(message.from_user.id)
    await config_update()
