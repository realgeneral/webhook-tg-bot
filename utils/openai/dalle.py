# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

import openai
import telegram
import os
import json
import httpx
import base64

from loader import bot, cache, db, config, _
from telebot import types
from utils.texts import Pluralize, split_text
from telebot.formatting import escape_markdown, escape_html
from keyboards.inline import BotKeyboard
from utils.limits import exceed_limit
from utils.strings import CacheData
from utils.logging import logging
from utils.balancing import BalancingKeys
from utils.message_loader import message_add_list, message_remove_list
from openai import AsyncOpenAI

ratios = {
    '1:1': {
        'mult': 1,
        'size': '1024x1024'
    },
    '9:16': {
        'mult': 2,
        'size': '1024x1792'
    },
    '16:9':  {
        'mult': 2,
        'size': '1792x1024'
    },
}

async def generate_image(
    user:      object,
    message:   object,
    user_type: str = 'user',
    variants:  int = config.getint('openai', 'dalle_variants')
):
    """ Обрабатывает пользовательский запрос к DALL-E

        :message:   object сообщение
        :user_type: str    тип юзера [user или chat]
        :variants:  dict   кол-во вариантов на основе одного запроса
    """
    telegram_id = message.from_user.id if user_type == 'user' else message.chat.id
    prompt = message.text

    user_subscribe = user['is_subscriber']

    variants = await cache.get(f'{message.from_user.id}_dalle_ratio') or '1:1'

    tokens_variants_price = config.getint('openai', 'dalle_request_tokens') * ratios.get(variants).get('mult')

    remaining_balance = (user['balance'] - tokens_variants_price)

    # Список с числительными для плюрализации
    numerals_tokens = _('numerals_tokens')

    # Если токены на балансе закончились, уведомляем
    if (
        user['balance'] < tokens_variants_price and
        config.getboolean('default', 'unlimited') is False and
        user['is_unlimited'] == False
    ):
        await exceed_limit(
            telegram_id,
            user['language_code'],
            (tokens_variants_price - user['balance']),
            key_string = 'remained_exceeded_limit' if type == 'user' else 'remained_exceeded_limit_chat',
            type = user_type
        )

        await bot.delete_state(message.from_user.id)

        await cache.delete(CacheData.dalle_generation.format(
            message.from_user.id
        ))

        return

    # При безлимитном режиме баланс остаётся тем же
    if config.getboolean('default', 'unlimited') or user['is_unlimited']:
        remaining_balance = user['balance']

    # Иницализируем класс распределения токенов
    balancer = BalancingKeys('openai', 50)

    # Берём ключ с наименьшим кол-вом соединений
    api_key = await balancer.get_available_key()

    try:
        if user_type == 'user':
            sent_message = await bot.send_message(
                message.chat.id,
                _('waiting_dalle')
            )
            await message_add_list(_('waiting_dalle'), message.chat.id, sent_message.message_id, user['language_code'], 'dalle')

        # Custom endpoint
        base_url = None
        if config.getboolean('openai', 'proxy_endpoint'):
            base_url = config.get('openai', 'proxy_endpoint_url')

        # Proxies
        http_client = None
        if config.getboolean('proxy', 'enabled'):
            http_client = httpx.AsyncClient(
                proxies = {
                    "http://":  config.get('proxy', 'http'),
                    "https://": config.get('proxy', 'http')
                },
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),
            )

        client = AsyncOpenAI(
            api_key=api_key, base_url=base_url,
            http_client=http_client, timeout=180
        )

        ratio_type = ratios.get(variants).get('size')
        response = await client.images.generate(
            prompt = prompt,
            n      = 1,
            size   = ratio_type,
            model = 'dall-e-3',
            #
            response_format = 'b64_json'
        )

        bot_info = await bot.get_me()
        text_for_caption = escape_html(prompt)
        share_text = _('image_additional_info').format(**{
            "request":  text_for_caption if len(prompt) < 800 else text_for_caption[0:850] + '...',
            "name":     bot_info.first_name,
            "username": bot_info.username,
            "model":    'DALL·E',
        })

        media_variants = []
        photo = None
        for n, u in enumerate(response.data):
            caption = share_text if n == 0 else ''
            photo = base64.b64decode(u.b64_json)
            media_variants.append(
                types.InputMediaPhoto(photo, caption=caption, parse_mode="HTML")
            )

        await message_remove_list(message.chat.id, sent_message.message_id, user['language_code'], 'dalle')

        if user_type == 'chat':
            await bot.send_media_group(
                chat_id             = message.chat.id,
                media               = media_variants,
                reply_to_message_id = message.id,
            )

        if user_type == 'user':
            await bot.delete_message(
                sent_message.chat.id,
                sent_message.message_id
            )
            # Если мы получаем ошибку по FloodAwaitError - нужно отправить ссылки на фотки или попросить пользователя подождать n-секунд
            try:
                await bot.send_media_group(
                    chat_id             = message.chat.id,
                    media               = media_variants,
                    reply_to_message_id = message.id
                )
                await bot.send_document(
                    message.chat.id,
                    (f'dalle_3_{ratio_type}.jpeg', photo),
                    caption = _('original_image_file')
                )
            except Exception as e:
                # await bot.send_message(
                #     chat_id = message.chat.id,
                #     reply_to_message_id = message.id,
                #     text = _('image_links').format(**{
                #         'links': "\n".join([
                #             f"<a href='{v}'>{_('image_link')} №{k}</a>\n" for k, v in enumerate(media_links, 1)
                #         ]),
                #         "request":  escape_html(prompt),
                #         "name":     bot_info.first_name,
                #         "username": bot_info.username,
                #         "model":    'DALL·E 3',
                #     }),
                #     parse_mode          = 'HTML'
                # )
                logging.warning(e)


            string_variants_price = Pluralize.declinate(tokens_variants_price, numerals_tokens)
            string_remaining_balance = Pluralize.declinate(remaining_balance, numerals_tokens, type=5)

            msg = _('dalle_anything_else').format(**{
                "amount_token": tokens_variants_price,
                "p1":           string_variants_price.word,
                "balance":      remaining_balance,
                "p2":           string_remaining_balance.word,
            })

            if config.getboolean('default', 'unlimited') or user['is_unlimited']:
                msg += _('unlimited_mode')

            await bot.send_message(
                chat_id      = message.chat.id,
                text         = msg,
                reply_markup = BotKeyboard.back_to_main_menu_dalle()
            )

            bot_unlim = config.getboolean('default', 'unlimited')
            unlimited_rq =  bot_unlim if bot_unlim else user['is_unlimited']
            await db.create_request(
                user['id'],
                0,
                'dalle',
                json.dumps(prompt),
                json.dumps(response.data[0].url),
                total_tokens = tokens_variants_price,
                unlimited    = int(config.getboolean('default', 'unlimited')),
                is_sub = user_subscribe
            )

    except Exception as e:
        # Удаляем ключ
        await message_remove_list(message.chat.id, sent_message.message_id, user['language_code'], 'dalle')

        msg = _('dalle_greeting_error')
        msg += _('error_request_for_admin').format(
            escape_markdown(str(e)[:1024])
        )

        # Сообщаем об ошибке
        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            parse_mode   = 'Markdown',
            reply_markup = BotKeyboard.back_to_main_menu_dalle()
        )
        # Выводим в debug
        print(e)

    # Освобождаем соединение для балансировщика
    await balancer.decrease_connection(api_key)
    # Очищаем состояние
    await bot.delete_state(message.from_user.id)
