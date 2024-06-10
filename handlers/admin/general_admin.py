# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config_path, config, _, u, loop
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, InputFile, InputMediaDocument
from datetime import datetime, timedelta
from telebot.formatting import escape_markdown
from telebot.util import extract_arguments
from keyboards.inline import BotKeyboard
from states.states import BotState, AdminUsers
from utils.strings import CallbackData, CacheData
from utils.texts import Pluralize
from utils.configurable import config_update
from utils.logging import logging
from io import BytesIO

import aiofiles
import json
import psutil
import re
import tempfile
import asyncio

async def admin_parse(message):
    """ Главная страница админки
    """

    mode_unlim = _('dict_unlimited_mode')
    mode_service = _('dict_service_status')

    msg = _('admin_start_text').format(**{
        'mode': mode_service[
            int(config.getboolean('default', 'unlimited'))
        ][2:].lower(),
    })
    kb = InlineKeyboardMarkup()

    kb.row(
        InlineKeyboardButton(_('inline_admin_openai'), callback_data=CallbackData.admin_openai),
        InlineKeyboardButton(_('inline_admin_keys'), callback_data=CallbackData.admin_keys),
    ).row(
        InlineKeyboardButton(_('inline_stable_diffusion'), callback_data=CallbackData.admin_stable),
        InlineKeyboardButton(_('inline_midjourney'), callback_data=CallbackData.admin_midjourney),
    ).row(
        InlineKeyboardButton(
            _('inline_admin_users'), callback_data=CallbackData.admin_users
        ),
        InlineKeyboardButton(
            _('inline_admin_pages'), callback_data=CallbackData.admin_pages
        )
    ).row(
        InlineKeyboardButton(
            _('inline_admin_promocodes'), callback_data=CallbackData.admin_promocodes
        ),
        InlineKeyboardButton(
            _('inline_admin_affiliate'), callback_data=CallbackData.admin_affiliate
        )
    ).row(
        InlineKeyboardButton(
            _('inline_admin_shop'), callback_data=CallbackData.admin_shop
        ),
        InlineKeyboardButton(
            _('inline_admin_payments'), callback_data=CallbackData.admin_view_payment
        ),
    ).row(
        InlineKeyboardButton(
            _('inline_channels'), callback_data=CallbackData.admin_channels
        ),
        InlineKeyboardButton(
            _('inline_admin_create_nl'), callback_data=CallbackData.admin_create_newsletter
        )
    ).row(
        InlineKeyboardButton(_('inline_admin_analytics'), callback_data=CallbackData.admin_analytics),
        InlineKeyboardButton(mode_unlim[int(config.getboolean('default', 'unlimited'))], callback_data=CallbackData.admin_unlimited_mode),
    ).row(
        InlineKeyboardButton(
            _('inline_back_to'), callback_data=CallbackData.user_home
        )
    )

    return msg, kb

admin_cancel_action_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton('Отменить действие', callback_data=CallbackData.admin_users)],
])

@bot.message_handler(is_chat=False, role=['admin'], commands=['load_telegram_ids'])
async def load_prompts_history(message):
    users = await db.get_raw("SELECT * FROM users")
    obj = None

    obj = BytesIO("\n".join([
        f"{i['telegram_id']}" for i in users if i['telegram_id'] > 1
    ]).encode())

    await bot.send_document(message.from_user.id, (f'users.txt', obj))

@bot.message_handler(is_chat=False, role=['admin'], commands=['load_users'])
async def load_prompts_history(message):
    users = await db.get_raw("SELECT * FROM users")
    obj = None

    obj = BytesIO("\n".join([
        f"{i['telegram_id']};@{i['username']};{i['created_at']}" for i in users if i['telegram_id'] > 1
    ]).encode())

    await bot.send_document(message.from_user.id, (f'users.txt', obj), caption="Telegram ID / Username / Join")

@bot.message_handler(is_chat=False, role=['admin'], commands=['load_requests'])
async def load_prompts_history(message):
    # system_dialogs = await db.get_dialog({
    #     'is_system': 1,
    #     'language_code': 'ru'
    # })
    # media = []
    # for dialog in system_dialogs:
    requests = await db.get_raw(f'SELECT type, message FROM requests')

    obj = BytesIO("\n".join([
        f"{i['type']} -> {i['message']}" for i in requests if len(i['message']) > 1
    ]).encode())

    await bot.send_document(message.from_user.id, (f'all_requests.txt', obj))

@bot.message_handler(is_chat=False, role=['admin'], commands=['edit_param'])
async def edit_param(message):
    """ Сервисная функция для изменения параметров, которые не были добавлены
        в админке для оказания быстрой поддержки по каким-то вопросикам
    """
    arguments = extract_arguments(message.text)
    arguments = arguments.split("+") if arguments else arguments

    msg = '❗️ Для изменения параметра в main.ini следуйте следующему формату: <b>/edit_param</b>  <i>директива+параметр+новое_значение</i>\n\nНе используйте эту команду без знаний типов данных, которые требуются для каждого параметра, в противном случае вы можете нарушить работу системы.'

    if arguments and len(arguments) < 3:
        msg = '❗️ Не указаны нужное кол-во аргументов для изменения параметра'

    if arguments and len(arguments) == 3:
        try:
            param = config.get(arguments[0], arguments[1])

            if arguments[0] in ['redis', 'mysql', 'webhook'] or arguments[1] in ['token']:
                raise Exception

            if arguments and param:
                msg = '✅ Значение параметра <b>{0}</b> в директивке <b>{1}</b> успешно изменено с <b>{2}</b> на <b>{3}</b>'.format(arguments[1], arguments[0], param, arguments[2])

                config.set(arguments[0], arguments[1], arguments[2])
                await config_update()
        except Exception as e:
            print(e)
            msg = '❗️ Директива или аргумент не найдены'


    await bot.send_message(
        message.from_user.id,
        msg,
        parse_mode = 'HTML'
    )

@bot.callback_query_handler(role=['admin', 'demo'], func=lambda call: call.data == CallbackData.admin_home, is_chat=False)
async def callback_handler(call):
    """ Админ панель по callback
    """
    await bot.delete_state(call.from_user.id)
    admin_msg, admin_keyboard = await admin_parse(call)

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=admin_msg,
        parse_mode="Markdown",
        reply_markup=admin_keyboard
    )

@bot.message_handler(is_chat=False, commands=['admin'], role=['admin', 'demo'])
async def callback_handler(message):
    """ Админ панель по команде /admin
    """

    await bot.delete_state(message.from_user.id)
    admin_msg, admin_keyboard = await admin_parse(message)

    await bot.send_message(
        chat_id=message.from_user.id,
        text=admin_msg,
        parse_mode="Markdown",
        reply_markup=admin_keyboard
    )

@bot.message_handler(is_chat=False, commands=['server'], role=['admin'])
async def callback_handler(message):
    """ Данные о сервере /server
    """
    memory = psutil.virtual_memory()

    available_memory = {
        'total': memory.total >> 20,
        'used':  memory.used >> 20,
    }

    msg = str(f'*💻 Данные о сервере*\n\n'
              f'Загрузка процессора: *{psutil.cpu_percent()}% / 100%*\n'
              f'Загрузка оперативной памяти: *{memory.percent}% / 100%*\n\n'
              f"RAM: *{available_memory['used']} Мб / {available_memory['total']} Мб*")

    await bot.send_message(
        chat_id=message.from_user.id,
        text=msg,
        parse_mode="Markdown",
    )

@bot.message_handler(is_chat=False, commands=['stop_newsletter'], role=['admin'])
async def stop_newsletter(message):
    """ Останавливает рассылку
    """
    await cache.set('stop_newsletter', 1)

@bot.callback_query_handler(func=lambda call: call.data == CallbackData.admin_create_newsletter, is_chat=False, role=['admin', 'demo'])
async def create_newsletter(call):
    """ Рассылка

        1. Ввод сообщения
    """
    await bot.edit_message_text(
        message_id   = call.message.message_id,
        chat_id      = call.message.chat.id,
        text         = _('admin_newsletter_text'),
        parse_mode   = "Markdown",
        reply_markup = admin_cancel_action_keyboard
    )

    await cache.set("newsletter_data_links", "")
    await bot.set_state(call.from_user.id, BotState.create_newsletter)


async def get_newsletter_data():
    """ Данные о рассылке
    """
    data = await cache.get("newsletter_data")
    link = await cache.get("newsletter_data_links")
    return {
        'data': json.loads(data) if data else None,
        'links': json.loads(link) if link else None
    }

async def send_newsletter(user_id = 0, newsletter = {}, parse_mode = 'HTML', mode = 'newsletter'):
    """ Отправляет сообщение из рассылки

        (по типу контента)
    """
    newsletter_data  = newsletter.get('data')
    newsletter_links = newsletter.get('links')
    kb = None

    if newsletter_links:
        links = []
        for i in newsletter_links:
            lnk = InlineKeyboardButton(i.get('name'))
            lnk.url = i.get('link')
            if i.get('link').startswith('_'):
                lnk.url = None
                lnk.callback_data = i.get('link')[1:]
            links.append([lnk])

        kb = InlineKeyboardMarkup(links)

    try:
        if newsletter_data.get("photo"):
            await bot.send_photo(
                chat_id      = user_id,
                photo        = newsletter_data.get("photo"),
                caption      = newsletter_data.get("caption", ''),
                reply_markup = kb,
                parse_mode   = parse_mode
            )
        elif newsletter_data.get("video"):
            # VIDEO
            await bot.send_video(
                chat_id      = user_id,
                video        = newsletter_data.get("video"),
                caption      = newsletter_data.get("caption", ''),
                reply_markup = kb,
                parse_mode   = parse_mode
            )
        elif newsletter_data.get("text"):
            # TEXT
            await bot.send_message(
                chat_id      = user_id,
                text         = newsletter_data.get("text", '^.^'),
                reply_markup = kb,
                parse_mode   = parse_mode
            )

        return True

    except Exception as e:
        if mode == 'newsletter':
            await bot.send_message(
                chat_id      = user_id,
                text         = str(e),
                reply_markup = kb,
                parse_mode   = None
            )
        print(e)

        return False


@bot.callback_query_handler(func=lambda call: call.data.startswith(CallbackData.start_newsletter), is_chat=False, role=['admin', 'demo'])
async def create_newsletter(call):
    """ Рассылка

        Отправка сообщений всем юзерам
    """
    type_param = call.data.replace(CallbackData.start_newsletter, '')
    type = {
        'all': "SELECT * FROM users WHERE type = 'user'",
        'sub': "SELECT * FROM users WHERE type = 'user' AND is_subscriber = 1",
        'free': "SELECT * FROM users WHERE type = 'user' AND is_subscriber = 0",
    }

    users = await db.get_raw(type.get(type_param, type.get('all')))
    users_count = int(len(users))

    async def update_info(call, message_id):
        await bot.edit_message_text(
            chat_id    = call.from_user.id,
            message_id = message_id,
            text       = f"⏳ Отправлено *{status}/{users_count}*\n\n"
                         f"❗️ Заблокировали бот: *{blocked}*\n\n"
                          "*Отправлено / Всего пользователей*.",
            parse_mode = 'Markdown'
        )

    semaphore = asyncio.Semaphore(10)
    async def send_newsletter_with_semaphore(user, call_user_id):
        async with semaphore:
            try:
                if user['telegram_id'] == call_user_id:
                    return False
                if await cache.get('stop_newsletter'):
                    return 'stopped'
                response = await send_newsletter(user['telegram_id'], newsletter, mode='user')
                if not response:
                    raise Exception(f"User #{user['telegram_id']} not found")
                if user['is_active'] == 0:
                    await db.update_user(
                        user['telegram_id'],
                        {'is_active': 1}
                    )

                await asyncio.sleep(0.33)

                return 'sent'
            except Exception as e:
                await db.update_user(
                    user['telegram_id'],
                    {'is_active': 0}
                )
                logging.warning(e)
                return 'blocked'

    if users_count == 0:
        await bot.answer_callback_query(
            call.id,
            'Нет пользователей для рассылки',
            show_alert=True
        )
        return

    newsletter = await get_newsletter_data()

    await bot.delete_message(
        call.from_user.id,
        call.message.message_id
    )
    start_newsletter = await bot.send_message(
        chat_id = call.from_user.id,
        text    = _('start_newsletter').format(**{
            'who': _('dict_type_newsletter').get(type_param)
        })
    )

    status = 0
    blocked = 0
    string_newsletter_type = 'done_newsletter'

    tasks = [send_newsletter_with_semaphore(user, call.from_user.id) for user in users]
    for task in asyncio.as_completed(tasks):
        result = await task
        if result == 'stopped':
            await cache.delete('stop_newsletter')
            string_newsletter_type = 'stop_newsletter'
            break
        elif result == 'sent':
            status += 1
            if status == 1:
                await update_info(call, start_newsletter.message_id)
            if status % 30 == 0:
                await update_info(call, start_newsletter.message_id)
        elif result == 'blocked':
            blocked += 1

    await update_info(call, start_newsletter.message_id)

    await bot.send_message(
        chat_id      = call.message.chat.id,
        text         = _(string_newsletter_type).format(**{
            'who': _('dict_type_newsletter').get(type_param)
        }),
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(_('inline_back_to'), callback_data='admin.back_to_home')],
        ])
    )

@bot.message_handler(state=BotState.create_newsletter, is_chat=False, content_types=['audio', 'animation', 'sticker', 'video_note', 'voice', 'contact', 'location', 'venue', 'dice', 'invoice', 'successful_payment'])
async def not_supported_message(message):
    """ Если пользователь отправил
        неподдерживаемый тип контента
        сообщаем ему об этом
    """
    user = await db.get_user(message.from_user.id)
    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = '❌ Этот тип контента не поддерживается ботом.\n\n'
                       'Для рассылки прикрепите текст, фото с текстом, видео с текстом одним сообщением.',
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(_('inline_back_to'), callback_data='admin.back_to_home')],
        ])
    )


@bot.callback_query_handler(func=lambda call: call.data == 'admin.send_newsletter_add_link', is_chat=False, role=['admin', 'demo'])
async def create_newsletter(call):
    """ Рассылка

        Добавение ссылки
    """
    await bot.send_message(
        chat_id      = call.message.chat.id,
        text         = _('admin_newsletter_add_link'),
        reply_markup = admin_cancel_action_keyboard
    )
    await bot.set_state(call.from_user.id, BotState.add_link_newsletter)

    async with bot.retrieve_data(call.from_user.id) as data:
        data['message_id'] = call.message.message_id

@bot.message_handler(state=BotState.add_link_newsletter, is_chat=False)
async def admin_handler_add_link_newsletter(message):
    """ Добавление ссылки
    """
    user = u.get()

    links = []
    for text in message.text.split('\n'): # rewrite
        args = re.split(",| ,|, ", text)
        if args is None or len(args) != 2:
            continue
        links.append({
            'name': args[0],
            'link': args[1].strip(),
        })

    if not links:
        await bot.send_message(
            chat_id      = message.chat.id,
            text         = "Укажите корректный формат ссылки\n\n"
                           "_Формат: название кнопки, ссылка_.",
            reply_markup = await BotKeyboard.newsletter()
        )
        return

    async with bot.retrieve_data(message.from_user.id) as data:
        data['message_id'] = message.message_id

    await cache.set("newsletter_data_links", json.dumps(links))

    newsletter = await get_newsletter_data()
    await send_newsletter(message.from_user.id, newsletter)

    await bot.send_message(
        chat_id      = message.chat.id,
        text         = "✅ Успешно прикреплено. Отправляем этот вариант?",
        reply_markup = await BotKeyboard.newsletter()
    )

    await bot.set_state(call.from_user.id, BotState.create_newsletter)

@bot.message_handler(state=BotState.create_newsletter, is_chat=False, content_types=['text', 'photo', 'video'])
async def admin_handler_create_newsletter(message):
    """ Обработчик рассылки юзерам
    """
    msg = {}

    if message.content_type == 'video':
        msg['caption']  = message.caption
        msg['video'] = message.video.file_id
        await cache.set("newsletter_data", json.dumps(msg))

    if message.content_type == 'photo':
        msg['caption']  = message.caption
        msg['photo'] = message.photo[-1].file_id
        await cache.set("newsletter_data", json.dumps(msg))

    if message.content_type == 'text':
        msg['text'] = message.text
        await cache.set("newsletter_data", json.dumps(msg))

    newsletter = await get_newsletter_data()
    await send_newsletter(message.from_user.id, newsletter)

    await bot.send_message(
        chat_id      = message.chat.id,
        text         = "Отправляем этот вариант?",
        reply_markup = await BotKeyboard.newsletter(),
        parse_mode   = 'Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == CallbackData.admin_unlimited_mode, is_chat=False, role=['admin', 'demo'])
async def callback_handler(call):
    """ Включение/отключение безлимта
    """
    mode = config.get('default', 'unlimited')
    new_value = 'False' if mode == 'True' else 'True'

    config.set('default', 'unlimited', new_value)
    await config_update()

    admin_msg, admin_keyboard = await admin_parse(call)
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=admin_msg,
        parse_mode="Markdown",
        reply_markup=admin_keyboard
    )

@bot.message_handler(is_chat=False, commands=['copyright'])
async def callback_handler(message):
    """ Copyright
    """
    await bot.send_message(
        chat_id=message.from_user.id,
        text = '*Коммерческий телеграм-бот @PremiumAiBot*\n\n'
               'Автор: Павел Зверев / @paulfake\n'
               'Канал: https://t.me/itsheriff\n'
               'Сайт: https://zverev.io/\n'
               'Почта: paschazverev@gmail.com'
    )
