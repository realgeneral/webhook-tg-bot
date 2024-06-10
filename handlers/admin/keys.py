# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.balancing import BalancingKeys
from states.states import AdminKeys
from telebot.formatting import escape_markdown
from utils.openai.chat_completion import chat_completion

async def parse_home_keys():
    """ Главное меню Ключи
    """
    msg = _('admin_keys')
    status = _('dict_str_status')

    kb = {}

    keys = await db.get_key()
    for key in keys:
        name = status[key['status']] + f" {key['service'].upper()} {key['key'][0:8]}...{key['key'][-8:]}"
        kb.update({
            name: {'callback_data': CallbackData.admin_key_view+str(key['id'])}
        })

    kb.update({
        _('inline_admin_key_create'): {'callback_data': CallbackData.admin_key_create},
        _('inline_back_to'): {'callback_data': CallbackData.admin_home},
    })

    return msg, BotKeyboard.smart(kb)

async def parse_edit_key(key_id):
    """ Главное меню редактирования Ключа
    """
    user = u.get()
    balancing = BalancingKeys()
    msg = _('admin_key_edit')
    status = _('dict_service_status')

    kb = {}

    key = await db.get_key({'id': key_id})
    key[0]['service'] = key[0]['service'].upper()

    key[0]['status'] = status[key[0]['status']]
    key[0]['active_connections'] = await balancing.get(key[0]['key']) or 0

    if not user['is_superuser']:
        key[0]['key'] = f"{key[0]['key'][0:8]}...{key[0]['key'][-8:]}"

    if key[0]['reason']:
        msg += _('key_reason').format(escape_markdown(key[0]['reason']))

    ek = CallbackData.admin_key_set_param + "{0}." + str(key[0]['id'])
    kb.update({
        key[0]['status']:    {'callback_data': ek.format('mode')},
        _('inline_delete'):  {'callback_data': ek.format('delete')},
        _('inline_back_to'): {'callback_data': CallbackData.admin_keys},
    })

    return msg.format(**key[0]), BotKeyboard.smart(kb)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_keys, role=['admin', 'demo'])
async def admin_home_keys(call):
    """ Главная настроек ключей
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_home_keys()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_key_view), role=['admin', 'demo'])
async def admin_edit_key(call):
    """ Настройка ключа
    """
    await bot.delete_state(call.from_user.id)

    key_id = call.data.replace(CallbackData.admin_key_view, '')
    msg, kb = await parse_edit_key(key_id)

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )
    await bot.delete_state(call.from_user.id)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_key_set_param), role=['admin'])
async def admin_edit_key(call):
    """ Изменение настроек ключа
    """
    raw_param = call.data.replace(CallbackData.admin_key_set_param, '').split('.')

    param  = raw_param[0]
    key_id = raw_param[1]
    key = await db.get_key({'id': key_id})
    balancing = BalancingKeys(key[0]['service'])

    if param == 'mode':
        status = 'inactive' if key[0]['status']  == 'active' else 'active'

        if key[0]['status'] == 'inactive':
            await balancing.create(key[0]['key'])
        elif key[0]['status'] == 'active':
            await balancing.delete(key[0]['key'])

        await db.update_key(key[0]['key'], {'status': status, 'reason': ''})
        msg, kb = await parse_edit_key(key_id)

    if param == 'delete':
        await bot.edit_message_text(
            chat_id      = call.from_user.id,
            message_id   = call.message.message_id,
            text         = _('delete_key').format(key[0]['key']),
            reply_markup = BotKeyboard.smart({
                _('inline_delete'): {'callback_data': CallbackData.admin_key_delete+key_id},
                _('inline_back_to'): {'callback_data': CallbackData.admin_key_view+key_id}
            })
        )
        return

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_key_delete), role=['admin'])
async def delete_key(call):
    """ Удаляет ключ
    """
    key_id = call.data.replace(CallbackData.admin_key_delete, '')

    key = await db.get_key({'id': key_id})
    balancing = BalancingKeys(key[0]['service'])

    await db.delete_object(table="keys", name_id="id", data=key_id)
    await balancing.delete(key[0]['key'])

    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_keys},
    })
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('delete_key_success'),
        reply_markup = kb
    )


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_key_create, role=['admin'])
async def create_key_1(call):
    """ Создание ключа

        1. Выбор сервиса
    """
    # перенести в config
    kb = {
        'OpenAi': {'callback_data': CallbackData.admin_create_key_service+'openai'},
        'Yandex SpeechKit': {'callback_data': CallbackData.admin_create_key_service+'ya_speechkit'},
        'Stable Diffusion': {'callback_data': CallbackData.admin_create_key_service+'stable_diffusion'},
        'Midjourney': {'callback_data': CallbackData.admin_create_key_service+'midjourney'},
        _('inline_back_to'): {'callback_data': CallbackData.admin_keys}
    }

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('choose_key_service'),
        reply_markup = BotKeyboard.smart(kb)
    )
    await bot.set_state(call.from_user.id, AdminKeys.A1)


@bot.callback_query_handler(is_chat=False, state=AdminKeys.A1, func=lambda call: call.data.startswith(CallbackData.admin_create_key_service), role=['admin'])
async def create_key_2(call):
    """ Создание ключа

        2. Сохранение сервиса и ввод ключа
    """
    service = call.data.replace(CallbackData.admin_create_key_service, '')

    async with bot.retrieve_data(call.from_user.id) as data:
        data['service'] = service

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('input_key_for_serivce').format(service.upper()),
        reply_markup = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_keys}
        })
    )
    await bot.set_state(call.from_user.id, AdminKeys.A2)

@bot.message_handler(is_chat=False, state=AdminKeys.A2, role=['admin'])
async def create_key_3(message):
    """ Создание ключа

        3. Проверка на корректность и сохранение ключа в базу
    """
    user = u.get()

    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_keys}
    })

    async with bot.retrieve_data(message.from_user.id) as data:
        service = data['service']
        balancing = BalancingKeys(service)

        if service == 'openai':
            check = await bot.send_message(
                chat_id = message.from_user.id,
                text = _('check_key_waiting')
            )

            completion, usage, errors = await chat_completion(
                api_key = message.text,
                prompt  = 'test'
            )

            if errors:
                msg = _('check_key_error').format(escape_markdown(" | ".join(errors)))
                await bot.edit_message_text(
                    chat_id      = message.from_user.id,
                    message_id   = check.message_id,
                    text         = msg,
                    reply_markup = kb
                )
                return

            await bot.edit_message_text(
                chat_id      = message.from_user.id,
                message_id   = check.message_id,
                text         = _('check_key_success').format(completion)
            )

        new_key = await db.create_key({
            'user_id': user['id'],
            'service': service,
            'key': message.text,
        })

        await balancing.create(message.text)

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = _('key_created'),
            reply_markup = BotKeyboard.smart({
                _('inline_get_edit'): {'callback_data': CallbackData.admin_key_view+str(new_key)},
                _('inline_back_to'): {'callback_data': CallbackData.admin_keys}
            })
        )

    await bot.delete_state(message.from_user.id)
