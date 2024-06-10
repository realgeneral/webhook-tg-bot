from loader import bot, cache, db, config_path, config, _, u, loop
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from keyboards.inline import BotKeyboard
from states.states import BotState
from utils.strings import CallbackData
from classes.user import Balance
from handlers.user.shop import get_tariff_name

import asyncio

async def parse_payment(payment: dict = {}) -> tuple:
    """ Отображает информацию о платеже
    """
    dict_currencies = _('dict_currency')
    dict_status = _('dict_payment_status')
    dict_types = _('dict_payment_type')

    kb = {}
    if payment.get('status') in ['pending', 'declined'] and payment.get('type') in ['tx']:
        kb.update({
            _('i_accept_payment'): {'callback_data':
                CallbackData.admin_accept_payment+f"{payment.get('id')}"
            }
        })

    payment['currency'] = dict_currencies[payment['currency']]
    payment['status'] = dict_status[payment['status']]
    payment['type'] = dict_types[payment['type']].format(**payment)
    payment['updated_at'] = payment['updated_at'] or '-'

    if payment.get('from_user_id') > 0:
        from_user = await db.get_user(user_id=payment.get('from_user_id'), name_id="id")
        payment['from_user_id'] = f"{from_user['telegram_id']} ({from_user.get('username', '-')})"
    else:
        payment['from_user_id'] = _('payment_system_user')

    if payment.get('user_id') > 0:
        from_user = await db.get_user(user_id=payment.get('user_id'), name_id="id")
        if from_user:
            payment['user_id'] = f"{from_user['telegram_id']} ({from_user.get('username', _('neurouser'))})"

    if payment.get('payment_provider_id') > 0:
        provider = await db.get_payment_provider({'id': payment['payment_provider_id']})
        payment['payment_provider_id'] = provider[0]['name']
    else:
        payment['payment_provider_id'] = '-'

    if payment.get('tariff_id') > 0:
        tariff = await db.get_tariff({'id': payment['tariff_id']})
        payment['tariff_id'] = get_tariff_name(tariff[0])
    else:
        payment['tariff_id'] = '-'

    kb.update({
        _('inline_back_to'): {'callback_data': CallbackData.admin_home}
    })

    return _('admin_payment_info').format(**payment), BotKeyboard.smart(kb)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_pay_txs, role=['admin', 'demo'])
async def admin_search_payment(call):
    """ Список последних успешных платежей
    """
    kb = {}

    payments = await db.get_payment(
        {'type': 'tx', 'status': 'success'},
        end_limit=15
    )

    if not payments:
        await bot.answer_callback_query(
            call.id,
            _('payments_not_found'),
            show_alert=True
        )
        return

    for p in payments:
        kb.update({
            f"№{p['id']} / {p['amount']} {p['currency']}": {'callback_data': CallbackData.admin_payment+str(p['id'])}
        })
    kb.update({
        _('inline_back_to'): {'callback_data': CallbackData.admin_shop}
    })

    await bot.edit_message_text(
        message_id   = call.message.message_id,
        chat_id      = call.message.chat.id,
        text         = _('list_success_txs'),
        reply_markup = BotKeyboard.smart(kb)
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_payment), role=['admin', 'demo'])
async def admin_search_payment(call):
    """ Платеж по callback
    """
    keyb = { _('inline_back_to'): {'callback_data': CallbackData.admin_pay_txs}}

    payment_id = call.data.replace(CallbackData.admin_payment, '')
    payment = await db.get_payment({'id': payment_id})

    msg, kb = await parse_payment(payment[0])

    await bot.edit_message_text(
        message_id   = call.message.message_id,
        chat_id      = call.message.chat.id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_accept_payment), role=['admin'])
async def accept_payment(call):
    """ Подтверждает платеж
    """
    balance = Balance(db = db)
    payment_id = call.data.replace(CallbackData.admin_accept_payment, '')

    accept_payment = await balance.accept_payment(payment_id)

    if accept_payment == False:
        await bot.answer_callback_query(
            call.id,
            _('payment_not_found'),
            show_alert=True
        )
        return

    payment = await db.get_payment({'id': payment_id})
    msg, kb = await parse_payment(payment[0])

    await bot.edit_message_text(
        message_id   = call.message.message_id,
        chat_id      = call.message.chat.id,
        text         = msg + '\n',
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_view_payment, role=['admin', 'demo'])
async def admin_search_payment(call):
    """ Поиск платежа
    """
    await bot.edit_message_text(
        message_id   = call.message.message_id,
        chat_id      = call.message.chat.id,
        text         = _('input_payment_id'),
        reply_markup = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_home},
        })
    )

    await bot.set_state(call.from_user.id, BotState.search_payment)

@bot.message_handler(is_chat=False, state=BotState.search_payment)
async def admin_view_payment(message):
    """ Поиск платежа
    """
    msg, kb = _('payment_not_found'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_home},
    })

    payment_id = message.text
    payment = await db.get_payment({'id': payment_id})

    if payment:
        msg, kb = await parse_payment(payment[0])
        await bot.delete_state(message.from_user.id)

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb
    )
