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
from states.states import AdminChannels
from telebot.formatting import escape_markdown
import re

async def add_channel(data):
    """ Добавляет канал в список
        для подписки

        :data:
    """
    if len(data.split('|')) != 2:
        return False

    channels = config.get('subscribe', 'channels')
    channels = [] if channels == 'False' else channels.split('\n')

    for d in channels:
        if d.startswith(data.split('|')[0]):
            return False

    channels.append(data)

    config.set('subscribe', 'channels', "\n".join(channels))
    await config_update()

    return True

async def parse_channels():
    """ Главное меню настройки каналов
    """
    user = u.get()

    service_status = _('dict_service_status')[config.getboolean('subscribe', 'required_subscribe')]

    gpt35turbo_unlim = _('dict_unlim_gpt35turbo')[config.getboolean('subscribe', 'unlim_gpt35turbo')]

    only_one_channel = _('dict_only_one_channel')[config.getboolean('subscribe', 'only_one_channel')]

    channels = config.get('subscribe', 'channels').split('\n') or _('channels_not_exist')

    msg = _('admin_channels').format(**{
        "mode": service_status,
        "mode_gpt": gpt35turbo_unlim,
        "mode_only_one_channel": only_one_channel,
    })

    kb = InlineKeyboardMarkup()

    kb.row(InlineKeyboardButton(
        service_status, callback_data=CallbackData.admin_channels_set_param+'required_subscribe'
    ))
    kb.row(InlineKeyboardButton(
        gpt35turbo_unlim, callback_data=CallbackData.admin_channels_set_param+'unlim_gpt35turbo'
    ))
    kb.row(InlineKeyboardButton(
        only_one_channel, callback_data=CallbackData.admin_channels_set_param+'only_one_channel'
    ))

    if channels[0] != 'False': # sorry
        for ch in channels:
           tg_url = config.get('default', 'telegram_url')
           status = _('dict_str_status')

           channel = ch.split("|")

           title = channel[0]
           username = channel[1]
           active = status['active']

           try:
               chat = await bot.get_chat(channel[0])
               member = await bot.get_chat_administrators(channel[0])

               title = chat.title
               username = tg_url + chat.username if chat.username else channel[1]
           except Exception as e:
               active = status['inactive']

           kb.row(
               InlineKeyboardButton(
                   f"{active} {title}",
                   url=str(username)
               ),
               InlineKeyboardButton(
                   '❌', callback_data=CallbackData.admin_delete_channel+channel[0]
               ),
           )

    kb.add(InlineKeyboardButton(
        _('inline_add_channel'), callback_data=CallbackData.admin_create_channel
    ))

    kb.add(InlineKeyboardButton(
        _('inline_back_to'), callback_data=CallbackData.admin_home
    ))

    return msg, kb



@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_create_channel, role=['admin'])
async def admin_channels(call):
    """ Добавление канала в список
    """
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('admin_create_channel_text'),
        reply_markup = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_channels}
        })
    )
    await bot.set_state(call.from_user.id, AdminChannels.A1)


@bot.message_handler(is_chat=False, content_types=['text', 'photo', 'animation'], state=AdminChannels.A1)
async def first_step_add_channel(message):
    """ Шаг 1. Добавление приватного/публичного канала/группы

        Публичный канал/группа добавляются сразу
        Для приватного действует переход на следующий этап (ввода инвайт ссылки)
    """
    msg = _('admin_chat_not_exist')
    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_channels}
    })

    message_from_chat = message.forward_from_chat

    chat_admin = False
    chat_id = 0

    type_chat = _('dict_chat_type')
    type_chat_added = _('dict_admin_chat_added')

    if message_from_chat:
        try:
            administrators = await bot.get_chat_administrators(message_from_chat.id)
            chat_admin = True
        except Exception as e:
            pass

        if chat_admin:
            chat_id = message_from_chat.id
            msg = _('admin_chat_added_link').format(**{
                'admin_chat_added': type_chat_added[message_from_chat.type],
                'type_chat': type_chat[message_from_chat.type],
                'id': chat_id,
                'title': message_from_chat.title,
            })
            async with bot.retrieve_data(message.from_user.id) as data:
                data['id'] = message_from_chat.id
                data['title'] = message_from_chat.title
            await bot.set_state(message.from_user.id, AdminChannels.A2)

    if not message_from_chat:

        channel_login = message.text.replace('https://t.me/', '').replace('http://t.me/', '')
        if not channel_login.startswith('@'): channel_login = "@" + channel_login

        try:
            administrators = await bot.get_chat_administrators(channel_login)
            chat_admin = True
        except Exception as e:
            pass

        if chat_admin:
            info = await bot.get_chat(channel_login)
            chat_id = info.id

            username = f"https://t.me/{channel_login.replace('@', '')}"
            channel_data = f'{chat_id}|{username}'

            msg = _('admin_chat_added').format(**{
                'admin_chat_added': type_chat_added[info.type],
                'type_chat': type_chat[info.type],
                'id': chat_id,
                'title': info.title,
            })

            added = await add_channel(channel_data)
            if added is False:
                msg = _('channel_exist_in_list')

            if added:
                await bot.delete_state(message.from_user.id)

    if chat_id == 0:
        msg = _('admin_chat_bot_not_admin')

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb
    )

@bot.message_handler(is_chat=False, state=AdminChannels.A2)
async def second_step_add_channel(message):
    """ Шаг 2.

        Добавление ссылки для приватного канала/приватной группы
    """
    channel_link = message.text
    url_pattern = pattern = r'^https?://[\w\-]+(\.[\w\-]+)+[/#?]?.*'

    type_chat = _('dict_chat_type')
    type_chat_added = _('dict_admin_chat_added')

    is_url = re.match(url_pattern, channel_link)
    added = False
    chat_info = None

    msg = _('url_not_valid')
    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_channels}
    })

    if is_url:
        async with bot.retrieve_data(message.from_user.id) as data:
            chat_info = await bot.get_chat(data['id'])
            added = await add_channel(f"{data['id']}|{channel_link}")
            if added is False: msg = _('channel_exist_in_list')

    if added:
        msg = _('admin_chat_added').format(**{
            'admin_chat_added': type_chat_added[chat_info.type],
            'type_chat': type_chat[chat_info.type],
            'id': chat_info.id,
            'title': chat_info.title,
        })
        await bot.delete_state(message.from_user.id)

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_delete_channel), role=['admin'])
async def delete_channel(call):
    """ Удаление канала из списка
    """
    channel_for_delete = call.data.replace(CallbackData.admin_delete_channel, '')
    channels = config.get('subscribe', 'channels').split('\n')

    for d in channels:
        if d.startswith(channel_for_delete):
            channels.remove(d)

    new_param = 'False' if not channels else "\n".join(channels)

    if not channels:
        config.set('subscribe', 'required_subscribe', 'False')

    config.set('subscribe', 'channels', new_param)
    await config_update()

    msg, kb = await parse_channels()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_channels, role=['admin', 'demo'])
async def admin_channels(call):
    """ Главная настройки каналов
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_channels()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_channels_set_param), role=['admin'])
async def update_channels_params(call):
    """ Обновляет настройки каналов
    """
    param = call.data.replace(CallbackData.admin_channels_set_param, '')
    msg, kb = _('service_disabled'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_channels}
    })

    if not param:
        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )

    if param in ['required_subscribe', 'unlim_gpt35turbo', 'only_one_channel']:
        channels = config.get('subscribe', 'channels')
        # Если каналов не существует
        if channels == 'False':
            await bot.answer_callback_query(
                call.id,
                _('channels_not_exist'),
                show_alert=True
            )
            return

        mode = config.get('subscribe', param)
        new_value = 'False' if mode == 'True' else 'True'
        config.set('subscribe', param, new_value)
        await config_update()
        msg, kb = await parse_channels()

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )
