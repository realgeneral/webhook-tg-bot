# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from states.states import AdminProvider
from utils.payment_providers import payment_drivers

async def parse_home_providers():
    """ Платежные системы
    """
    msg = _('admin_payment_providers')
    dict_status = _('dict_str_status')
    kb = {}

    providers = await db.get_payment_provider({})
    for provider in providers:
        name = dict_status[provider['status']] + f" {provider['name']}"
        kb.update({
            name: {'callback_data': CallbackData.admin_provider.new(provider_id=provider['id'])}
        })

    kb.update({
        _('inline_back_to'): {'callback_data': CallbackData.admin_shop}
    })

    return msg, BotKeyboard.smart(kb)

async def parse_edit_provider(provider_id):
    """ Главное меню редактирования провайдераа
    """
    msg = _('admin_provider_edit')
    status = _('dict_service_status')
    status_ap = _('dict_tariff_autopayment_status')
    status_webapp = _('dict_provider_webapp_popup')

    provider = await db.get_payment_provider({'id': provider_id})
    if not provider:
        return

    driver = payment_drivers[provider[0]['slug']]

    provider[0]['status'] = status[provider[0]['status']]
    provider[0]['ap'] = status_ap[provider[0]['autopayments']]
    provider[0]['webapp_popup'] = status_webapp.get(provider[0]['webapp_popup'])

    kb = {}
    edit_provider = CallbackData.admin_provider_set_param + "{0}." + str(provider_id)

    kb.update({
        _('inline_admin_tariff_change_name'): {'callback_data': edit_provider.format('name')},
        _('inline_admin_change_api_token'): {'callback_data': edit_provider.format('payment_token')},
        _('inline_admin_change_data'): {'callback_data': edit_provider.format('data')},
        provider[0]['webapp_popup']: {'callback_data': edit_provider.format('webapp_popup')},
        provider[0]['status']: {'callback_data': edit_provider.format('mode')},

    })

    if driver.autopayment():
        kb.update({
            status_ap[provider[0]['autopayments']]: {'callback_data': edit_provider.format('autopayments')},
        })

    kb.update({
        _('inline_back_to'): {'callback_data': CallbackData.admin_shop_providers},
    })

    return msg.format(**provider[0]), BotKeyboard.smart(kb)


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_shop_providers, role=['admin', 'demo'])
async def admin_home_providers(call):
    """ Платежные провайдеры
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_home_providers()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda x: x.data.startswith(CallbackData.admin_provider.new(provider_id='')), role=['admin'])
async def admin_edit_provider(call):
    """ Настройка провайдера
    """
    provider = CallbackData.admin_provider.parse(callback_data=call.data)
    msg, kb = await parse_edit_provider(provider['provider_id'])

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )
    await bot.delete_state(call.from_user.id)


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_provider_set_param), role=['admin'])
async def admin_edit_provider(call):
    """ Изменение настроек ключа
    """
    raw_param = call.data.replace(CallbackData.admin_provider_set_param, '').split('.')

    param  = raw_param[0]
    provider_id = raw_param[1]
    provider = await db.get_payment_provider({'id': provider_id})

    msg, kb = '-', BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_provider.new(provider_id=provider_id)}
    })

    if param == 'mode':
        status = 'inactive' if provider[0]['status']  == 'active' else 'active'
        await db.update_payment_provider(provider_id, {'status': status})
        msg, kb = await parse_edit_provider(provider_id)

    if param in ['autopayments', 'webapp_popup']:
        status = 0 if provider[0][param] == 1 else 1
        await db.update_payment_provider(provider_id, {param: status})
        msg, kb = await parse_edit_provider(provider_id)

    if param in ['name', 'payment_token', 'data']:
        dict_param = _('dict_provider_params').get(param)
        msg = _('input_new_value_param').format(dict_param)

        await bot.set_state(call.from_user.id, AdminProvider.A1)
        async with bot.retrieve_data(call.from_user.id) as data:
            data['provider_id'] = provider_id
            data['param'] = param

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.message_handler(is_chat=False, state=AdminProvider.A1, role=['admin'])
async def save_and_check_provider_param(message):
    """ Сохранение настроек провайдера
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text
        provider_id = data['provider_id']

        param = data['param']
        dict_param = _('dict_provider_params')[param]
        msg = _('param_value_updated').format(dict_param)

        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_provider.new(provider_id=provider_id)}
        })
        #
        # if param in ['data']:
        #     try:
        #         new_val = int(new_val)
        #     except Exception as e:
        #         new_val = 0

        if param in ['payment_token']:
            provider = await db.get_payment_provider({'id': provider_id})
            driver = payment_drivers[provider[0]['slug']](
                api_token=new_val,
                provider=provider[0]
            )

            information = await driver.get_information()
            if not information:
                msg = _('payment_token_not_update').format(provider[0]['name'])
                await bot.send_message(
                    chat_id      = message.from_user.id,
                    text         = msg,
                    reply_markup = kb,
                )
                return

        await db.update_payment_provider(provider_id, {param: new_val})
        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )
    await bot.delete_state(message.from_user.id)
