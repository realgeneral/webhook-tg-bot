# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config as cfg, _, u
from utils.openai import dalle
from states.states import BotState, CreateDialog
from keyboards.inline import BotKeyboard
from telebot.util import extract_arguments
from utils.texts import Pluralize
from utils.strings import CallbackData, CacheData
from utils.configurable import get_lock
import json

async def dalle_request(message):
    """ Req in DALL-E
    """
    generate_redis_key = CacheData.dalle_generation.format(message.from_user.id)
    generate = await cache.get(generate_redis_key)

    if generate is not None:
        await bot.send_message(
            message.from_user.id,
            _('waiting_dalle_generation')
        )
        return

    lock = await get_lock(message.from_user.id)
    async with lock:
        await cache.set(generate_redis_key, 1)
        await cache.expire(generate_redis_key, 30)
        await dalle.generate_image(u.get(), message)

    await cache.delete(generate_redis_key)

async def parse_dalle(data: str = "", user_id: int = 0, same: bool = False):
    """ Парсит главную DALL-E

        :data:    str callback.data
        :user_id: int
        :inline:  bool
    """
    data = data.replace(CallbackData.dalle, "")
    dalle_ratio = await cache.get(f'{user_id}_dalle_ratio') or '1:1'

    user = u.get()
    current_ratio = dalle_ratio

    if same:
        if data.startswith('#ratio_'):
            try:
                dalle_ratio = data.replace("#ratio_", "")
            except Exception as e:
                pass

        # Сохраняем в кэш новое значене
        if current_ratio != dalle_ratio:
            await cache.set(f'{user_id}_dalle_ratio', dalle_ratio)

    tokens_variants = cfg.getint('openai', 'dalle_request_tokens') * int(dalle.ratios.get(dalle_ratio).get('mult'))

    requests_count = int(round(
        user.get('balance', 0) / tokens_variants,
        1 # format: 0 / 12 / 11
    ))

    numerals_requests = _('numerals_requests')
    variants_requests = Pluralize.declinate(requests_count, numerals_requests)

    numerals_tokens = _('numerals_tokens')
    variants = Pluralize.declinate(tokens_variants, numerals_tokens)

    ratio_info = _('dict_aspect_ratios').get(dalle_ratio)
    msg = _('dalee_greeting').format(**{
        "variants":        1,
        "variants_tokens": tokens_variants,
        "p1":              variants.word,
        # Request's count
        "request_count":   requests_count,
        "r1":              variants_requests.word,
        "ratio":           dalle_ratio,
        "desc_ratio":      ratio_info.get('text'),
        "img_url":         ratio_info.get('dalle_link')
    })

    return msg, BotKeyboard.dalle_configuration(dalle_ratio), same

@bot.message_handler(is_chat=False, commands=['dalle'], service='dalle', stats='dalle_command', is_subscription=True)
async def dalle_command_handler(message, data):
    """ Главная DALL-E по команде /start
    """
    user = data['user']

    text = message.text.replace('/dalle ', '').replace('/dalle', '')
    if len(text) > 4:
        await dalle_request(message)
        return

    msg, kb, same = await parse_dalle(user_id = message.from_user.id)

    await bot.send_message(
        chat_id=message.from_user.id,
        text=msg,
        reply_markup=kb,
        disable_web_page_preview=False,
    )
    await bot.set_state(message.from_user.id, BotState.generate_image)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.dalle), service='dalle', stats='dalle_callback', is_subscription=True)
async def dalle_callback_query_handler(call, data):
    """ Главная DALL-E по callback query
    """
    user = data['user']
    msg, kb, same = await parse_dalle(
        call.data,
        user_id = call.from_user.id,
        same = True
    )

    if same is False:
        return

    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        parse_mode   = "Markdown",
        reply_markup = kb,
        disable_web_page_preview=False,
    )
    await bot.set_state(call.from_user.id, BotState.generate_image)

@bot.message_handler(is_chat=False, state=BotState.generate_image, service='dalle', is_subscription=True, content_types=['voice', 'video', 'sticker', 'document', 'video_note', 'audio', 'location', 'contact', 'pinned_message', 'animation'])
async def gpt_dialog_not_supported_content(message, data):
    await bot.send_message(
        chat_id  = message.from_user.id,
        text     = _('dalle_not_supported_content')
    )

@bot.message_handler(is_chat=False, state=BotState.generate_image, service='dalle', is_subscription=True, content_types=['text'], continue_command='dalle')
async def dalle_handler(message):
    """ Обработка запроса DALL-E

    """
    await dalle_request(message)
