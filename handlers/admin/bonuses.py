# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u, loop
from languages.language import lang_variants
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from states.states import AdminBon
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.configurable import config_update

async def parse_bonuses():
    """ Главное меню настройки ежедневных бонусом
    """
    service_status = _('dict_service_status')[config.getboolean('bonuses', 'status')]
    service_notify_status = _('dict_notify_status')[config.getboolean('bonuses', 'notification')]

    msg = _('admin_bonuses').format(**{
        "mode":  service_status,
        "notification": service_notify_status,
        "min_balance": config.get('bonuses', 'min_balance'),
        "bonus": config.get('bonuses', 'bonus'),
        "time_bonus": config.get('bonuses', 'time_bonus'),
        "time_burn_bonus": config.get('bonuses', 'time_burn_bonus'),
    })

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(_('inline_parameters'), callback_data='_')
    ).row(
        InlineKeyboardButton(
            service_status, callback_data=CallbackData.admin_bon_set_param+'status'
        ),
    ).row(
        InlineKeyboardButton(
            service_notify_status, callback_data=CallbackData.admin_bon_set_param+'notification'
        ),
    ).row(
        InlineKeyboardButton(_('inline_min_balance'), callback_data=CallbackData.admin_bon_set_param+'min_balance')
    ).row(
        InlineKeyboardButton(_('inline_bonus'), callback_data=CallbackData.admin_bon_set_param+'bonus')
    ).row(
        InlineKeyboardButton(
            _('inline_back_to'), callback_data=CallbackData.admin_users
        )
    )

    return msg, kb

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_bonuses, role=['admin', 'demo'])
async def admin_bonuses(call):
    """ Главная настроек бонусов
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_bonuses()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_bon_set_param), role=['admin'])
async def update_bonuses_settings(call):
    """ Обновляет настройки бонусов
    """
    param = call.data.replace(CallbackData.admin_bon_set_param, '')
    msg, kb = _('service_disabled'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_bonuses}
    })

    if not param:
        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )

    directive = 'bonuses'

    if param in ['status', 'notification']:
        mode = config.get(directive, param)
        new_value = 'False' if mode == 'True' else 'True'
        config.set(directive, param, new_value)
        await config_update()
        msg, kb = await parse_bonuses()

    if param in ['min_balance', 'bonus']:
        dict_param = _('dict_config_params')[param]
        msg = _('input_new_value_param').format(dict_param)

        await bot.set_state(call.from_user.id, AdminBon.A1)

        async with bot.retrieve_data(call.from_user.id) as data:
            data['param'] = param

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.message_handler(is_chat=False, state=AdminBon.A1, role=['admin'])
async def admin_chatgpt_create_dialog(message):
    """ Сохранение настроек бонусов
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text

        param = data['param']
        dict_param = _('dict_config_params')[param]

        msg = _('param_value_updated').format(dict_param)
        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_bonuses}
        })

        if param in ['min_balance', 'bonus']:
            try:
                new_val = int(new_val)
            except Exception as e:
                new_val = 0

        config.set('bonuses', param, str(new_val))

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )

    await bot.delete_state(message.from_user.id)
    await config_update()
