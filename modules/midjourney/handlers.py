# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2024, Павел Зверев

from loader import bot, cache, db, config as cfg, _, u, root_dir, bmode

from .driver import MidjourneyGoApi
from .configuration import midjourney_user_config, midjourney_update_config
from .misc import upload_telegram_files, IMAGES_DIR

from keyboards.inline import BotKeyboard
from telebot.util import extract_arguments
from telebot.formatting import escape_html, escape_markdown
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputMediaPhoto
from telebot.asyncio_handler_backends import State, StatesGroup

from utils.texts import Pluralize
from states.states import MidjourneyState, EditMjParam
from utils.strings import CallbackData, CacheData
from utils.balancing import BalancingKeys
from utils.message_loader import message_add_list, message_remove_list
from utils.limits import exceed_limit
from utils.logging import logging
from utils.configurable import get_lock
from telebot import types
from PIL import Image

import telegram
import datetime
import json
import asyncio
import base64
import aiohttp
import aiofiles
import os
import io

mjdata = 'mj#'
base_url = f"https://{cfg.get('webhook', 'host')}:{cfg.get('webhook', 'port')}"

user_locks = {}

async def split_image(image, output_folder = IMAGES_DIR, task = {}):
    """ Upscale 4 картинок от MJ
    """
    img = Image.open(io.BytesIO(image), mode = 'r')
    width, height = img.size
    target_width = width // 2
    target_height = height // 2

    coordinates = [
        (0, 0, target_width, target_height),
        (target_width, 0, width, target_height),
        (0, target_height, target_width, height),
        (target_width, target_height, width, height)
    ]

    tasks = []
    for i, (left, upper, right, lower) in enumerate(coordinates):
        part_img = img.crop((left, upper, right, lower))
        filename = f"{task.get('task_id')}_{i+1}.jpeg"

        t = asyncio.create_task(save_image(part_img, f"{output_folder}/{filename}"))
        tasks.append(t)

    await asyncio.gather(*tasks)

async def save_image(img, output_path):
    img.save(output_path)

async def parse_midjourney(message):
    msg = _('midjourney_greeting')
    numerals_requests = _('numerals_requests')
    ratios = _('dict_aspect_ratios')

    user = u.get()
    mj_cfg = await midjourney_user_config(message.from_user.id)

    kb = InlineKeyboardMarkup()

    kb.row(
        InlineKeyboardButton(_('i_change_version'), callback_data='editmjparam#edit_version'),
        InlineKeyboardButton(_('i_change_aspect_ratio'), callback_data='editmjparam#edit_aspect_ratio'),
    )
    kb.row(
        InlineKeyboardButton(_('i_mj_info'), web_app=types.WebAppInfo(cfg.get('midjourney', 'info_link')))
    )
    kb.row(
        InlineKeyboardButton(_('inline_back_to'), callback_data=CallbackData.user_home)
    )

    requests_price = {
        # text to image
        'tti':int(round(
            user.get('balance', 0) / cfg.getint('midjourney', 'tti_price'), 0
        ))

    }

    mj_cfg['price_tti'] = cfg.getint('midjourney', 'tti_price')
    mj_cfg['r1'] = Pluralize.declinate(requests_price['tti'], numerals_requests).word
    mj_cfg['requests_tti'] = requests_price['tti']

    mj_cfg['version'] = mj_cfg['version']
    mj_cfg['ratio_description'] = ratios.get(mj_cfg.get('ratio'), ratios.get('1:1')).get('text')

    return msg.format(**mj_cfg), kb

async def mj_waiting_task(telegram_id = 0, action = 'get'):
    pattern = f'{telegram_id}_mj_waiting'

    if action == 'get':
        return await cache.get(pattern)

    if action == 'set':
        await cache.set(pattern, 1)
        await cache.expire(pattern, 180)
        return True

    if action == 'drop':
        return await cache.delete(pattern)

    return False


async def mj_check_balance(action):
    """ Проверяет баланс
    """
    user = u.get()
    balance = user['balance']

    response = {
        'status': True,
        'need_balance': 0,
        'price': 0
    }

    price = cfg.getint('midjourney', 'tti_price')
    need_balance = price - balance

    if action.startswith(('upscale1', 'upscale2', 'upscale3', 'upscale4')):
        price = cfg.getint('midjourney', 'base_upscale_price')

    if action.startswith((
        'variation', 'pan', 'retry', 'imagine', 'image-to-image',
        'blend', 'low_variation', 'high_variation', 'outpaint',
        'upscale_',
    )):
        price = cfg.getint('midjourney', 'tti_price')

    response['price'] = price

    if balance < price:
        response['need_balance'] = need_balance
        response['status'] = False

    if response['status']:
        await db.set_raw(f"""
            UPDATE users SET balance = balance - {price} WHERE id = {user['id']}
        """)

    return response

def midjourney_keyabord(task_id, task_type, allow_actions = []):
    """ Клавиатура у Midjourney изображений
    """
    kb = {}
    mj_str_action = 'mj_action#{0}|{1}'

    midjourney_actions = _('dict_midjourney_actions')
    imagine_btns = [
        'upscale1', 'upscale2',
        'upscale3', 'upscale4',
        'variation1', 'variation2',
        'variation3', 'variation4',
        'retry'
    ]
    actions_only = [
        'upscale1', 'upscale2',
        'upscale3', 'upscale4',
        'upscale2x', 'upscale4x',
        'vary_subtle', 'vary_subtle',
        'upscale_creative', 'upscale_subtle',
        'high_variation', 'low_variation',
        'outpaint_1.5x', 'outpaint_2x', 'outpaint_custom',
        'pan_down', 'pan_left', 'pan_right', 'pan_up'
    ]


    if task_type.startswith(('imagine', 'variation', 'reroll', 'retry', 'pan', 'blend', 'image-to-image', 'high_variation', 'low_variation', 'outpaint_')):
        for i in imagine_btns:
            kb.update({
                midjourney_actions.get(i, i).get('name'): {
                    'callback_data': mj_str_action.format(
                        i, task_id
                    )
                }
            })
        return BotKeyboard.smart(kb, 4)

    if task_type in actions_only:
        kb = InlineKeyboardMarkup()

        if all(action in allow_actions for action in ['upscale_creative', 'upscale_subtle']):
            kb.row(
                InlineKeyboardButton(
                    'Upscale (Subtle)',
                    callback_data=mj_str_action.format(
                        'upscale_subtle', task_id
                    )
                ),
                InlineKeyboardButton(
                    'Upscale (Creative)',
                    callback_data=mj_str_action.format(
                        'upscale_creative', task_id
                    )
                ),
            )

        if all(action in allow_actions for action in ['high_variation', 'low_variation']):
            kb.row(
                InlineKeyboardButton(
                    'Vary (Low)',
                    callback_data=mj_str_action.format(
                        'low_variation', task_id
                    )
                ),
                InlineKeyboardButton(
                    'Vary (High)',
                    callback_data=mj_str_action.format(
                        'high_variation', task_id
                    )
                ),
            )

        if all(action in allow_actions for action in ['outpaint_1.5x', 'outpaint_2x', 'outpaint_custom']):
            kb.row(
                InlineKeyboardButton(
                    'Zoom Out 2x',
                    callback_data=mj_str_action.format(
                        'outpaint_2', task_id
                    )
                ),
                InlineKeyboardButton(
                    'Zoom Out 1.5x',
                    callback_data=mj_str_action.format(
                        'outpaint_1.5', task_id
                    )
                ),
                InlineKeyboardButton(
                    'Custom Zoom',
                    callback_data=mj_str_action.format(
                        'outpaint_1', task_id
                    )
                ),
            )

        if all(action in allow_actions for action in ['pan_down', 'pan_left', 'pan_right', 'pan_up']):
            kb.row(
                InlineKeyboardButton(
                    '⬅️',
                    callback_data=mj_str_action.format(
                        'pan_left', task_id
                    )
                ),
                InlineKeyboardButton(
                    '➡️',
                    callback_data=mj_str_action.format(
                        'pan_right', task_id
                    )
                ),
                InlineKeyboardButton(
                    '⬆️',
                    callback_data=mj_str_action.format(
                        'pan_up', task_id
                    )
                ),
                InlineKeyboardButton(
                    '⬇️',
                    callback_data=mj_str_action.format(
                        'pan_down', task_id
                    )
                ),
            )
        return kb

    return None

async def mj_failed_task(task_id):
    """ Отпрваляет отправление об ошибке
    """

    task = await db.get_raw(f"""
        SELECT * FROM midjourney_tasks WHERE task_id = "{task_id}";
    """)

    if not task:
        return False

    task = task[0]
    message_data = task.get('message_data')

    try:
        await bot.delete_message(
            message_id = message_data.get('message_id'),
            chat_id    = message_data.get('chat_id'),
        )
    except Exception as e:
        pass

    await db.set_raw(f"""
        UPDATE users SET balance = balance + {task['tokens']} WHERE id = {task['user_id']}
    """)

    await message_remove_list(message_data.get('chat_id'), message_data.get('message_id'), message_data.get('lang'), 'midjourney')

    await bot.send_message(
        chat_id = message_data.get('chat_id'),
        text = _('mj_task_failed').format(**{
            "error": 'prompt error'
        }),
        reply_markup = BotKeyboard.smart({
            _('inline_mj_create_image'): {"callback_data": CallbackData.midjourney}
        }),
        parse_mode = 'HTML'
    )

async def mj_send_image(task_id, image_urls = None):
    """ Отпрваляет фото пользователю
    """
    task = await db.get_raw(f"""
        SELECT * FROM midjourney_tasks WHERE task_id = "{task_id}";
    """)

    if not task:
        return False

    task = task[0]
    bot_info = await bot.get_me()

    allow_actions = task.get('actions').split(',')
    message_data = task.get('message_data')

    file = b'\x00'
    if not task.get('file_id'):
        async with aiohttp.ClientSession() as session:
            data = await session.get(task.get('image_url'))
            file = await data.read()
            # await split_image(file, task = task)
    else:
        file = task.get('file_id')

    kb = None
    doc_file = task.get('doc_file_id')

    # Удаляем лок для следующих запросов
    await mj_waiting_task(telegram_id = message_data.get('chat_id'), action = 'drop')

    try:
        await bot.delete_message(
            message_id = message_data.get('message_id'),
            chat_id    = message_data.get('chat_id'),
        )
    except Exception as e:
        pass

    try:
        # Формирование медиа-группы для DOC
        # doc_caption = _('original_image_file', message_data.get('lang')) if not image_urls else _('original_image_with_upscale_files', message_data.get('lang'))
        doc_caption = _('original_image_file', message_data.get('lang'))

        doc_list = []
        media_group = None

        if not doc_file and type(file) == bytes:
            doc_list.append(
                types.InputMediaDocument((f'midjourney_{datetime.datetime.now()}.jpeg', file), caption=doc_caption)
            )

        if type(file) != bytes and doc_file:
            doc_file = doc_file.split(',')
            for f in enumerate(doc_file, start = 1):
               doc_list.append(
                   types.InputMediaDocument(f[1], caption=doc_caption)
               )
        #
        # if not doc_file and [1, 2, 3, 4]: # sorry
        #     for link in enumerate(image_urls, start = 1):
        #         filename = f"{task.get('task_id')}_{link[0]}.jpeg"
        #         async with aiofiles.open(IMAGES_DIR + filename, mode='rb') as f:
        #             f = await f.read()
        #             doc_list.append(
        #                 types.InputMediaDocument((f'upscale{link[0]}_{datetime.datetime.now()}.jpeg', f), caption=None)
        #             )

        photo = await bot.send_photo(
            photo   = file,
            chat_id = message_data.get('chat_id'),
            caption = _('mj_additional_info').format(**{
                'request':  MidjourneyGoApi.parse_prompt(
                    task.get('prompt')[0:800],
                    message_data.get('lang')
                ),
                "name":     bot_info.first_name,
                "username": bot_info.username,
                "model":    'Midjourney',
                "image_url": task.get('image_url'),
            }),
            reply_markup = midjourney_keyabord(task.get('id'), task.get('task_type'), allow_actions),
            parse_mode = 'HTML'
        )

        await message_remove_list(message_data.get('chat_id'), message_data.get('message_id'), message_data.get('lang'), 'midjourney')

        try:
            media_group = await bot.send_media_group(
                chat_id = message_data.get('chat_id'),
                media = doc_list,
            )
        except Exception as e:
            pass

        numerals_tokens = _('numerals_tokens')
        user = await db.get_raw(f"SELECT * FROM users WHERE telegram_id = {message_data.get('chat_id')}")
        await bot.send_message(
            chat_id = message_data.get('chat_id'),
            text = _(
                'chatgpt_tokens_usage'
            ).format(**{
                "amount_token": task.get('tokens'),
                "p1": Pluralize.declinate(task.get('tokens'), numerals_tokens).word,
                "balance": user[0]['balance'],
                "p2": Pluralize.declinate(user[0]['balance'], numerals_tokens, type=5).word,
            }),
            reply_markup = BotKeyboard.smart({
                _('inline_mj_create_image'): {'callback_data': CallbackData.midjourney}
            })
        )

        if not task.get('file_id') or not task.get('doc_file_id'):
            doc_file_ids = []
            for n in media_group:
                doc_file_ids.append(
                    n.document.file_id
                )

            await db.mj_update_task(
                task.get('task_id'),
                {
                    'file_id': photo.photo[-1].file_id,
                    'doc_file_id': ",".join(doc_file_ids),
                }
            )
    except Exception as e:
        await bot.send_message(
            chat_id = message_data.get('chat_id'),
            text = _('image_links').format(**{
                'link': f"<a href='{task.get('image_url')}'>{_('image_link')}</a>\n",
                "name":     bot_info.first_name,
                "username": bot_info.username,
                "model":    'Midjourney',
            }),
            reply_markup = midjourney_keyabord(task.get('id'), task.get('task_type'), allow_actions),
            parse_mode = 'HTML'
        )
        logging.warning(e)

# @bot.message_handler(is_chat=False, commands=['midjourney_update_tasks'], service='midjourney', is_subscription=True, stats='mj_home')
# async def mj_command(message):
#     """ Для оживления
#     """
#     msg, kb = await parse_midjourney(message)
#
#     from modules.midjourney.driver import MidjourneyGoApi
#     #     schedule.every(15).seconds.do(MidjourneyGoApi().tracking)
#
#     await bot.set_state(message.from_user.id, MidjourneyState.A1)

@bot.message_handler(is_chat=False, commands=['mj', 'midjourney'], service='midjourney', is_subscription=True, stats='mj_home')
async def mj_command(message):
    """ Главная MidJourney по команде /mj
    """
    msg, kb = await parse_midjourney(message)
    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = 'HTML'
    )

    await bot.set_state(message.from_user.id, MidjourneyState.A1)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.midjourney, service='midjourney', is_subscription=True, stats='mj_home')
async def mjcall(call, data):
    msg, kb = await parse_midjourney(call)
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = 'HTML',
    )
    await bot.set_state(call.from_user.id, MidjourneyState.A1)

@bot.message_handler(is_chat=False, state=MidjourneyState.A1,  service='midjourney', content_types=['photo', 'text'], is_subscription=True, stats='mj_request')
async def midjourney_message_handler(message, data):
    """ Обрабатывает запрос к MJ
    """
    lock = await get_lock(message.from_user.id)

    mj_error_types = _('dict_midjourney_error_types')
    waiting_mj = _('waiting_mj')

    user = u.get()
    prompt = '-' if not message.text else message.text

    mode = 'imagine'
    download_files_message_id = None
    msg_creating_image = None
    file_ids  = []
    photos    = []
    filenames = []

    async with lock:
        mj_cfg = await midjourney_user_config(message.from_user.id)

        # Если есть активный запрос - останавливаем текущий
        if await mj_waiting_task(telegram_id = message.from_user.id) is not None:
            await bot.send_message(
                chat_id      = message.from_user.id,
                text         = _('mj_lock_request'),
            )
            return

        # Выбираю файлики из media group
        if data.get('media_group'):
            for file in data.get('media_group'):
                if file.photo:
                    if file.caption: prompt = file.caption
                    file_ids.append(file.photo[-1].file_id)

        # Если была прикреплена медиа-группа, но без фото
        if data.get('media_group') and not file_ids:
            await bot.send_message(
                message.from_user.id,
                _('mj_no_photo')
            )
            return False

        # Если не передана медиа-группа, а передано фото - беру его
        if not data.get('media_group') and message.photo:
            prompt = message.caption
            file_ids.append(
                message.photo[-1].file_id
            )

        # Выставляю mode (криво, как и всё тут, но...)
        if len(file_ids) == 1:
            mode = 'image-to-image'
            waiting_mj = _('mj_iti_waiting')
        elif len(file_ids) > 1:
            mode = 'blend'
            waiting_mj = _('mj_blend_waiting')

        balance = await mj_check_balance(mode)
        if balance.get('status') is False:
            await exceed_limit(
                message.from_user.id,
                user['language_code'],
                balance.get('need_balance'),
                key_string = 'remained_exceeded_limit',
                type = 'user'
            )
            return False

        # Если file_ids не пуст - загружаю все картинки
        # Они будут переданы MJ для скачивания
        if file_ids:
            tmp_message = await bot.send_message(
                message.from_user.id,
                _('download_images')
            )
            download_files_message_id = tmp_message.message_id
            photos, filenames = await upload_telegram_files(file_ids)

        # Удаляю информацию о скачивании файлов
        if download_files_message_id:
            try:
                await bot.delete_message(
                    chat_id = message.from_user.id,
                    message_id = download_files_message_id
                )
            except Exception as e:
                pass

        try:
            balancer = BalancingKeys('midjourney', 50)
            api_key = await balancer.get_available_key()

            if not api_key:
                raise Exception(_('error_key_not_exist'))

            service = MidjourneyGoApi(api_key)
            # Корректирую промпт
            prompt = MidjourneyGoApi.prompt_correction(prompt)

            # cref / sref
            extra_with_link = any(action in prompt for action in ['--cref http', '--sref http'])
            extra_without_link = any(action in prompt for action in ['--cref', '--sref'])

            if extra_without_link and not extra_with_link:
                photo_url = " ".join(photos)
                if '--cref' in prompt:
                    prompt = prompt.replace('--cref', f'--cref {photo_url}')
                if '--sref' in prompt:
                    prompt = prompt.replace('--sref', f'--sref {photo_url}')

            # Добавляю ссылку на картинку в самое начало промпта
            if not extra_without_link and mode == 'image-to-image':
                prompt = f"""{" ".join(photos)} {prompt}"""

            # Пишем о том, что проверяем промпт
            msg_creating_image = await bot.reply_to(
                message,
                _('check_prompt_mj')
            )

            # Проверяем промпт у GoAPI
            prompt_checker = await service.prompt_checker(prompt)
            if len(prompt_checker.get('ErrorMessage', [])) > 0:
                raise Exception(
                    mj_error_types.get('prompt_not_verify').format(prompt_checker.get('ErrorMessage'))
                )

            # Пишем, что генерируем изображение
            msg_creating_image = await bot.edit_message_text(
                chat_id      = message.from_user.id,
                message_id   = msg_creating_image.message_id,
                text         = waiting_mj,
            )
            await message_add_list(waiting_mj, message.chat.id, msg_creating_image.message_id, user['language_code'], 'midjourney')

            # Отправляем задачу в GoAPI
            resp = await service.imagine(
                prompt = prompt,
                mode   = mode,
                photos = photos,
                cfg    = mj_cfg
            )
            if resp.get('status') != 'success':
                raise Exception(
                    mj_error_types.get('imagine_error').format(resp.get('message'))
                )

            # Локаю все последующие возможные запросы
            await mj_waiting_task(telegram_id = message.from_user.id, action = 'set')

            # Создаём таску в базе
            await db.mj_create_task({
                'user_id':       user['id'],
                'task_id':       resp.get('task_id'),
                'task_type':     mode,
                'prompt':        prompt,
                'tokens':        balance.get('price', 0),
                'images':        ",".join(filenames),
                'message_data': {
                    'chat_id': message.chat.id,
                    'message_id': msg_creating_image.message_id,
                    'lang': user['language_code']
                }
            })

        except Exception as e:
            logging.warning(e)

            await db.set_raw(f"""
                UPDATE users SET balance = balance + {balance.get('price', 0)} WHERE id = {user['id']}
            """)

            # Удаляем лок для следующих запросов
            await mj_waiting_task(telegram_id = message.from_user.id, action = 'drop')

            if msg_creating_image:
                await message_remove_list(message.chat.id, msg_creating_image.message_id, user['language_code'], 'midjourney')

            error_request_msg = _('error_request')
            error_request_msg += _('error_request_for_admin').format(
                escape_markdown(str(e))[:1024]
            )

            await bot.send_message(
                chat_id             = message.from_user.id,
                text                = error_request_msg,
                reply_to_message_id = message.message_id,
                reply_markup        = BotKeyboard.smart({
                    _('inline_back_to_mj'): {'callback_data': CallbackData.midjourney}
                }),
            )

@bot.callback_query_handler(is_chat=False, func=lambda c: c.data.startswith('mj_action#'), service='midjourney', is_subscription=True, stats='mj_task_action')
async def midjourney_action(call):
    """ Выполняет задачу
    """
    lock = await get_lock(call.from_user.id)

    async with lock:
        user = u.get()
        balancer = BalancingKeys('midjourney', 50)

        data = call.data.replace('mj_action#', '')
        action, task_id = data.split('|')

        balance = await mj_check_balance(action)
        if balance.get('status') is False:
            await bot.answer_callback_query(
                call.id,
                _('need_tokens_per_request').format(**{
                    'tokens': balance.get('need_balance'),
                }),
                show_alert = True
            )
            return False

        task = await db.get_raw(f"""
            SELECT * FROM
                midjourney_tasks
            WHERE
                id = {task_id} AND
                user_id = {user['id']}
        """)

        if not task:
            await bot.answer_callback_query(
                call.id,
                f"Task ID ({task_id}) not found",
                show_alert=True
            )
            return False

        task = task[0]
        origin_task_id = await db.get_raw(f"""
            SELECT * FROM
                midjourney_tasks
            WHERE
            	origin_task_id = "{task['task_id']}" AND
            	task_type = "{action}"
        """)

        # Отправляем результат, если задача была сгененирована ранее
        if origin_task_id and origin_task_id[0]['status'] == 'finished':
            await mj_send_image(origin_task_id[0]['task_id'])
            return

        # Если есть активный запрос - останавливаем текущий
        if await mj_waiting_task(telegram_id = call.from_user.id) is not None:
            await bot.answer_callback_query(
                call.id,
                _('mj_lock_request'),
                show_alert = True
            )
            return

        api_key = await balancer.get_available_key()
        service = MidjourneyGoApi(api_key)

        message_action = _('dict_midjourney_actions').get(action)

        try:
            new_task = await service.task_action(
                origin_task_id = task['task_id'],
                action         = action,
            )

            if new_task.get('status') == 'failed':
                raise Exception(new_task.get('message'))

            if new_task.get('status') == 'success':
                message_loader = await bot.reply_to(
                    message = call.message,
                    text    = message_action.get('message'),
                )

                # Удаляем анимацию / экшены о загрузке
                await message_add_list(message_action.get('message'), call.message.chat.id, message_loader.message_id, user['language_code'], 'midjourney')

                # Локаю все последующие возможные запросы
                await mj_waiting_task(telegram_id = call.from_user.id, action = 'set')

                # Создаём таску в базе
                await db.mj_create_task({
                    'user_id':        user['id'],
                    'origin_task_id': task['task_id'],
                    'task_id':        new_task.get('task_id'),
                    'tokens':         balance.get('price', 0),
                    'task_type':      action,
                    'prompt':         '-',
                    'message_data': {
                        'chat_id':    call.message.chat.id,
                        'message_id': message_loader.message_id,
                        'lang':       user['language_code']
                    }
                })
        except Exception as e:
            logging.warning(e)

            await db.set_raw(f"""
                UPDATE users SET balance = balance + {balance.get('price', 0)} WHERE id = {user['id']}
            """)

            # Удаляем лок для следующих запросов
            await mj_waiting_task(telegram_id = call.from_user.id, action = 'drop')
            await bot.answer_callback_query(
                call.id,
                _('mj_task_undefined'),
                show_alert=True
            )


@bot.message_handler(is_chat=False, state=MidjourneyState.A1, content_types=['audio', 'animation', 'sticker', 'video_note', 'voice', 'contact', 'location', 'venue', 'dice', 'invoice', 'successful_payment'], is_subscription=True)
async def midjourney_conenct_not_allowed(message, data):
    await bot.send_message(
        message.from_user.id,
        _('mj_no_photo')
    )

@bot.callback_query_handler(is_chat=False, func=lambda c: c.data.startswith('setmjparam#'))
async def midjourney_edit_param(call):
    param = call.data.replace('setmjparam#', '').split('|')
    key, val = param[0], param[1]
    await midjourney_update_config(call.from_user.id, key, val)
    # Data
    msg, kb = await parse_midjourney(call)
    parse_mode = 'HTML'

    if key == 'ratio':
        msg, kb = await parse_mj_edit_ratio(call)
        parse_mode = 'Markdown'

    # Send data
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = parse_mode,
        disable_web_page_preview = False,
    )

async def parse_mj_edit_ratio(message):
    mj_config = await midjourney_user_config(message.from_user.id)
    ratios = _('dict_aspect_ratios')

    msg = f"{_('choose_mj_param_aspect_ratio')}\n\n".format(**{
        "link": ratios.get(mj_config.get('ratio'), ratios.get('1:1')).get('mj_link')
    })
    kb = {}

    presets = cfg.get('midjourney', 'aspect_ratios')
    for i in presets.split(','):
        msg += f"*{i}* — {ratios.get(i, ratios.get('1:1')).get('text')}.\n"
        cname = i
        if str(mj_config.get('ratio')) == i:
            i = '✅ ' + i
        kb.update({
            i: {
                'callback_data': 'setmjparam#ratio|' + str(cname)
            }
        })
    kb.update({
     _('inline_back_to_mj'): {
         'callback_data': CallbackData.midjourney
     }
    })

    return msg, BotKeyboard.smart(kb, row_width=2)

@bot.callback_query_handler(is_chat=False, func=lambda c: c.data.startswith('editmjparam#'))
async def midjourney_edit_param(call):
    param = call.data.replace('editmjparam#', '')
    mj_config = await midjourney_user_config(call.from_user.id)

    kb = {}

    if param in ['edit_version']:
        msg = _('choose_mj_param_version')
        presets = cfg.get('midjourney', 'versions')
        for i in presets.split(','):
            name = i
            if str(mj_config.get('version')) == i:
                name = '✅ ' + name
            kb.update({
                name: {
                    'callback_data': 'setmjparam#version|' + str(i)
                }
            })

    kb.update({
        _('inline_back_to_mj'): {
            'callback_data': CallbackData.midjourney
        }
    })
    kb = BotKeyboard.smart(kb, row_width=2)

    if param in ['edit_aspect_ratio']:
        msg, kb = await parse_mj_edit_ratio(call)

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        disable_web_page_preview = False,
    )

@bot.message_handler(is_chat=False, state=EditMjParam.A1, content_types=['text'], is_subscription=True)
async def midjourney_save_params(message):
    """ Изменяет настройки Midjourney
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        try:
            param = data['param']
            val = message.text
            params = {'edit_step': 'steps', 'edit_cfg_scale': 'cfg_scale'}

            try:
                if param in ['edit_step']:
                    val = int(val)
                    if val < 10 or val > 50: val = 50
            except Exception as e:
                val = 50

            try:
                if param in ['edit_cfg_scale']:
                    val = int(val)
                    if val < 0 or val > 35: val = 10
            except Exception as e:
                val = 10

            key, val = params.get(param), val
            await midjourney_update_config(message.from_user.id, key, val)
            # Data
            msg, kb = await parse_midjourney(message)
            # Send data
            await bot.send_message(
                chat_id      = message.from_user.id,
                text         = msg,
                reply_markup = kb
            )
        except Exception as e:
            print(e)

    # Состояние
    await bot.set_state(message.from_user.id, SdState.active)
