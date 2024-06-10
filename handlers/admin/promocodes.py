# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, root_dir, config as cfg, u, _
from keyboards.inline import BotKeyboard
from telebot.formatting import escape_markdown
from utils.strings import CallbackData
from states.states import AdminPromocodes
import json
import os
from pathlib import Path
from datetime import datetime


async def parse_home_promocodes():
    """ Главное меню промокоды
    """
    msg = _('admin_promocodes')
    status = _('dict_str_status')

    kb = {}
    promocodes = await db.get_promocode({'status': 'active'}, end_limit=20)

    for code in promocodes:
        promocode = f"{status[code['status']]} {code['code']}"
        kb.update({
            promocode: {'callback_data': CallbackData.admin_promocode_view+str(code['id'])}
        })

    kb.update({
        _('inline_admin_promocode_create'): {'callback_data': CallbackData.admin_promocode_create},
        _('inline_back_to'): {'callback_data': CallbackData.admin_home},
    })

    return msg, BotKeyboard.smart(kb)


async def parse_edit_promocode(promocode_id):
    """ Главное меню редактирования промокода
    """
    msg = _('admin_promocode_edit')
    status = _('dict_service_status')


    kb = {}
    promocode = await db.get_promocode({'id': promocode_id})
    promocode = promocode[0]

    count = await db.get_raw(f'''
        SELECT COUNT(*) as count FROM payments WHERE type = "promocode" AND `label` = "{promocode['code']}"
    ''')

    promocode['status'] = status[promocode['status']]
    promocode['remaining_usage'] = count[0]['count'] or 0


    ek = CallbackData.admin_promocode_set_param + "{0}." + str(promocode['id'])

    kb.update({
        promocode['status']: {'callback_data': ek.format('mode')},
        _('inline_delete'):  {'callback_data': ek.format('delete')},
        _('inline_back_to'): {'callback_data': CallbackData.admin_promocodes},
    })

    return msg.format(**promocode), BotKeyboard.smart(kb)


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_promocodes, role=['admin', 'demo'])
async def admin_pages_list(call):
    """ Главная промокодов
    """
    msg, kb = await parse_home_promocodes()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_promocode_view), role=['admin', 'demo'])
async def admin_edit_promocode(call):
    """ Настройка ключа
    """
    key_id = call.data.replace(CallbackData.admin_promocode_view, '')
    msg, kb = await parse_edit_promocode(key_id)

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )
    await bot.delete_state(call.from_user.id)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_promocode_set_param), role=['admin'])
async def admin_edit_key(call):
    """ Изменение настроек ключа
    """
    raw_param = call.data.replace(CallbackData.admin_promocode_set_param, '').split('.')

    param  = raw_param[0]
    promocode_id = raw_param[1]
    promocode = await db.get_promocode({'id': promocode_id})

    if param == 'mode':
        status = 'inactive' if promocode[0]['status']  == 'active' else 'active'
        await db.update_promocode(promocode[0]['id'], {'status': status})
        msg, kb = await parse_edit_promocode(promocode_id)

    if param == 'delete':
        await bot.edit_message_text(
            chat_id      = call.from_user.id,
            message_id   = call.message.message_id,
            text         = _('delete_promocode').format(promocode[0]['code']),
            reply_markup = BotKeyboard.smart({
                _('inline_delete'): {'callback_data': CallbackData.admin_promocode_delete+promocode_id},
                _('inline_back_to'): {'callback_data': CallbackData.admin_promocode_view+promocode_id}
            })
        )
        return

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_promocode_delete), role=['admin'])
async def delete_key(call):
    """ Удаляет ключ
    """
    promocode_id = call.data.replace(CallbackData.admin_promocode_delete, '')
    # promocode = await db.get_promocode({'id': key_id})

    await db.delete_object(table="promocodes", name_id="id", data=promocode_id)

    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_promocodes},
    })
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('delete_promocode_success'),
        reply_markup = kb
    )


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_promocode_create, role=['admin'])
async def create_pm_1(call):
    """ Создание промокода

        1. Ввод кода
    """
    # После добавления mj перенести в config
    kb = {
        _('inline_back_to'): {'callback_data': CallbackData.admin_promocodes}
    }

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('choose_promocode'),
        reply_markup = BotKeyboard.smart(kb)
    )
    await bot.set_state(call.from_user.id, AdminPromocodes.A1)


@bot.message_handler(is_chat=False, state=AdminPromocodes.A1, role=['admin'])
async def create_pm_2(message):
    """ Создание проокода

        2. Сохранение кода и ввод номинала
    """
    user = u.get()

    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_promocodes}
    })

    if len(message.text) < 3 or len(message.text) > 56:
        await bot.send_message(
            chat_id = message.from_user.id,
            text = _('error_input_code'),
            reply_markup = kb
        )
        return

    async with bot.retrieve_data(message.from_user.id) as data:
        data['code'] = message.text

    await bot.send_message(
        chat_id = message.from_user.id,
        text = _('choose_promocode_amount').format(message.text),
        reply_markup = kb
    )

    await bot.set_state(message.from_user.id, AdminPromocodes.A2)

@bot.message_handler(is_chat=False, state=AdminPromocodes.A2, role=['admin'])
async def create_pm_3(message):
    """ Создание проокода

        3. Сохранение номинала и ввод кол-ва использований
    """
    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_promocodes}
    })

    user = u.get()

    try:
        amount = int(message.text)
    except Exception as e:
        amount = 1000

    if amount < 1:
        await bot.send_message(
            chat_id = message.from_user.id,
            text = _('error_input_code'),
            reply_markup = kb
        )
        return

    async with bot.retrieve_data(message.from_user.id) as data:
        data['amount'] = amount

    await bot.send_message(
        chat_id = message.from_user.id,
        text = _('choose_promocode_usage').format(message.text),
        reply_markup = kb
    )

    await bot.set_state(message.from_user.id, AdminPromocodes.A3)

@bot.message_handler(is_chat=False, state=AdminPromocodes.A3, role=['admin'])
async def create_pm_2(message):
    """ Создание проокода

        3. Создание промокода
    """
    user = u.get()
    usage = 0

    try:
        usage = int(message.text)
    except Exception as e:
        usage = 1

    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_promocodes}
    })

    async with bot.retrieve_data(message.from_user.id) as data:
        try:
            service = data['code']
            new_code = await db.create_promocode({
                'user_id': user['id'],
                'code': data['code'].upper(),
                'usage': usage,
                'amount': data['amount'],
                'status': 'active',
            })
            await bot.send_message(
                chat_id      = message.from_user.id,
                text         = _('promocode_created'),
                reply_markup = BotKeyboard.smart({
                    _('inline_get_edit'): {'callback_data': CallbackData.admin_promocode_view+str(new_code)},
                    _('inline_back_to'): {'callback_data': CallbackData.admin_promocodes}
                })
            )
        except Exception as e:
            print(e)

    await bot.delete_state(message.from_user.id)
