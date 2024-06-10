# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from states.states import AdminTariffs
from languages.language import lang_variants
from handlers.user.shop import get_tariff_name

async def parse_home_tariffs(msg_key: str = 'admin_tariffs', status: str = 'active', data_back_button: str = CallbackData.admin_shop):
    """ Тарифы
    """
    msg = _(msg_key)
    dict_status = _('dict_str_status')
    dict_currencies = _('dict_currency')

    kb = []

    tariffs = await db.get_tariff({'status': status})
    for tariff in tariffs:
        # name = dict_status[tariff['status']] + f" {tariff['name']} / {tariff['amount']} {dict_currencies[tariff['currency']]}"
        name = dict_status[tariff['status']] + ' ' + get_tariff_name(tariff)
        kb.append(InlineKeyboardButton(
            name,
            callback_data=CallbackData.admin_tariff.new(tariff_id=tariff['id'])
        ))

    kb = BotKeyboard.create_inline_keyboard(kb, row_width=1)

    if msg_key == 'admin_tariffs':
        kb.row(
            InlineKeyboardButton(
                _('inline_admin_tariff_archive'),
                callback_data=CallbackData.admin_tariff_archive
            ),
            InlineKeyboardButton(
                _('inline_admin_tariff_create'),
                callback_data=CallbackData.admin_tariff_create
            )
        )

    kb.add(InlineKeyboardButton(
        _('inline_back_to'),
        callback_data=data_back_button
    ))

    return msg, kb

async def parse_edit_tariff(tariff_id):
    """ Главное меню редактирования тарифа
    """
    msg = _('admin_tariff_edit')
    status = _('dict_tariff_status')
    currencies = _('dict_currency')
    type = _('dict_tariff_type')


    tariff = await db.get_tariff({'id': tariff_id})
    tariff[0]['status'] = status[tariff[0]['status']]
    tariff[0]['currency'] = currencies[tariff[0]['currency']]
    tariff[0]['type_tariff'] = type['sub'] if tariff[0]['days_before_burn'] > 0 else type['unlim']

    kb = {}

    edit_tariff = CallbackData.admin_tariff_set_param + "{0}." + str(tariff[0]['id'])
    kb.update({
        _('inline_admin_tariff_change_name'): {'callback_data': edit_tariff.format('name')},
        _('inline_admin_tariff_change_tokens'): {'callback_data': edit_tariff.format('tokens')},
        _('inline_admin_tariff_change_price'): {'callback_data': edit_tariff.format('amount')},
        _('inline_admin_tariff_change_dbb'): {'callback_data': edit_tariff.format('days_before_burn')},
        tariff[0]['status']: {'callback_data': edit_tariff.format('mode')},
        _('inline_back_to'): {'callback_data': CallbackData.admin_shop_tariffs},
    })

    return msg.format(**tariff[0]), BotKeyboard.smart(kb)


@bot.callback_query_handler(func=lambda call: call.data == CallbackData.admin_tariff_archive, is_chat=False, role=['admin', 'demo'])
async def callback_handler(call):
    """ Архив тарифов
    """
    msg, kb = await parse_home_tariffs(status='inactive', msg_key='admin_archive_tariffs', data_back_button=CallbackData.admin_shop_tariffs)
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=msg,
        parse_mode="Markdown",
        reply_markup=kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_shop_tariffs, role=['admin', 'demo'])
async def admin_home_tariffs(call):
    """ Главная настроек тарифов
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_home_tariffs()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda x: x.data.startswith(CallbackData.admin_tariff.new(tariff_id='')), role=['admin', 'demo'])
async def admin_edit_tariff(call):
    """ Настройка тарифа
    """
    tariff = CallbackData.admin_tariff.parse(callback_data=call.data)
    msg, kb = await parse_edit_tariff(tariff['tariff_id'])

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )
    await bot.delete_state(call.from_user.id)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_tariff_set_param), role=['admin'])
async def admin_edit_tariff(call):
    """ Изменение настроек ключа
    """
    raw_param = call.data.replace(CallbackData.admin_tariff_set_param, '').split('.')

    param  = raw_param[0]
    tariff_id = raw_param[1]
    tariff = await db.get_tariff({'id': tariff_id})

    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_tariff.new(tariff_id=tariff_id)}
    })

    if param == 'mode':
        status = 'inactive' if tariff[0]['status']  == 'active' else 'active'
        await db.update_tariff(tariff_id, {'status': status})
        msg, kb = await parse_edit_tariff(tariff_id)

    if param in ['tokens', 'name', 'amount', 'days_before_burn']:
        dict_param = _('dict_tariff_params')[param]
        msg = _('input_new_value_param').format(dict_param)

        await bot.set_state(call.from_user.id, AdminTariffs.A1)
        async with bot.retrieve_data(call.from_user.id) as data:
            data['tariff_id'] = tariff_id
            data['param'] = param

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )


@bot.message_handler(is_chat=False, state=AdminTariffs.A1, role=['admin', 'demo'])
async def update_tariff_param(message):
    """ Сохранение настроек тарифа
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text
        tariff_id = data['tariff_id']
        param = data['param']
        dict_param = _('dict_tariff_params')[param]
        msg = _('param_value_updated').format(dict_param)
        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_tariff.new(tariff_id=tariff_id)}
        })
        if param in ['amount', 'tokens']:
            try:
                new_val = float(new_val)
            except Exception as e:
                new_val = 0
        await db.update_tariff(tariff_id, {param: new_val})
        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )
    await bot.delete_state(message.from_user.id)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_tariff_create, role=['admin'])
async def create_tariff_1(call):
    """ Создание тарифа

        1. Выбор языкового кода
    """
    kb = {
        _('name', i): {'callback_data': CallbackData.admin_tc_cc + i}
        for i in lang_variants
    }
    kb.update({_('inline_back_to'): {'callback_data': CallbackData.admin_shop_tariffs}})

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('admin_tariff_create_1'),
        reply_markup = BotKeyboard.smart(kb)
    )
    await bot.set_state(call.from_user.id, AdminTariffs.B1)

@bot.callback_query_handler(is_chat=False, state=AdminTariffs.B1, func=lambda call: call.data.startswith(CallbackData.admin_tc_cc), role=['admin'])
async def create_tariff_2(call):
    """ Создание тарифа

        2. Ввод кол-ва токенов в тарифе
    """
    lang_code = call.data.replace(CallbackData.admin_tc_cc, '')

    async with bot.retrieve_data(call.from_user.id) as data:
        data['lang_code'] = lang_code

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('admin_tariff_create_2'),
        reply_markup = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_shop_tariffs}
        })
    )
    await bot.set_state(call.from_user.id, AdminTariffs.B2)

@bot.message_handler(is_chat=False, state=AdminTariffs.B2, role=['admin'])
async def create_tariff_3(message):
    """ Создание тарифа

        3. Выбор валюты
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        try:
            data['tokens'] = int(message.text)
        except Exception as e:
            data['tokens'] = 100

    kb = {
        v: {'callback_data': CallbackData.admin_tc_cc + k}
        for k, v in _('dict_currency').items()
    }
    kb.update({
        _('inline_back_to'): {'callback_data': CallbackData.admin_shop_tariffs}
    })

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = _('admin_tariff_create_3'),
        reply_markup = BotKeyboard.smart(kb)
    )
    await bot.set_state(message.from_user.id, AdminTariffs.B3)


@bot.callback_query_handler(is_chat=False, state=AdminTariffs.B3, func=lambda call: call.data.startswith(CallbackData.admin_tc_cc), role=['admin'])
async def create_tariff_4(call):
    """ Создание тарифа

        4. Ввод стоимости тарифа
    """
    currency = call.data.replace(CallbackData.admin_tc_cc, '')
    msg = '_'
    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_shop_tariffs}
    })

    async with bot.retrieve_data(call.from_user.id) as data:
        data['currency'] = currency
        msg = _('admin_tariff_create_4').format(**{'currency': _('dict_currency')[currency]})

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )
    await bot.set_state(call.from_user.id, AdminTariffs.B4)

@bot.message_handler(is_chat=False, state=AdminTariffs.B4, role=['admin'])
async def create_tariff_5(message):
    """ Создание тарифа

        5. Последний этап
    """
    kb = BotKeyboard.smart({
        _('inline_admin_tariff_create'): {'callback_data': CallbackData.admin_tariff_crfinal},
        _('inline_back_to'): {'callback_data': CallbackData.admin_shop_tariffs}
    })

    async with bot.retrieve_data(message.from_user.id) as data:
        try:
            data['amount'] = float(message.text)
        except Exception as e:
            data['amount'] = 100.00

        msg = _('admin_tariff_create_5').format(**{
            'tokens': data['tokens'],
            'amount': data['amount'],
            'currency': _('dict_currency')[data['currency']],
            'country': _('name', data['lang_code'])
        })

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb
        )


@bot.callback_query_handler(is_chat=False, state=AdminTariffs.B4, func=lambda call: call.data.startswith(CallbackData.admin_tariff_crfinal), role=['admin'])
async def create_tariff_4(call):
    """ Создание тарифа

        Сохранение в бд
    """
    user = u.get()
    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_shop_tariffs}
    })

    async with bot.retrieve_data(call.from_user.id) as data:
        try:
            tid = await db.create_tariff({
                'user_id':             user['id'],
                'language_code':       data['lang_code'],
                'name':                _('admin_tariff_name').format(data['tokens']),
                'tokens':              data['tokens'],
                'amount':              data['amount'],
                'currency':            data['currency'],
            })
            msg, kb = await parse_edit_tariff(tid)
            await bot.send_message(
                chat_id      = call.from_user.id,
                text         = _('tariff_created')
            )
            await bot.send_message(
                chat_id      = call.from_user.id,
                text         = msg,
                reply_markup = kb
            )
        except Exception as e:
            print(e)
    await bot.delete_state(call.from_user.id)
