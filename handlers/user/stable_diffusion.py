# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config as cfg, _, u
from keyboards.inline import BotKeyboard
from telebot.util import extract_arguments
from telebot.formatting import escape_html
from utils.texts import Pluralize
from utils.logging import logging
from states.states import EditStableParam
from utils.strings import CallbackData, CacheData
from utils.stable_diffusion import StableDiffusion
from utils.balancing import BalancingKeys
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputMediaPhoto
from telebot.asyncio_handler_backends import State, StatesGroup
from utils.message_loader import message_add_list, message_remove_list

from utils.limits import exceed_limit
from utils.strings import CacheData

from utils.configurable import get_lock

import telegram
import json
import asyncio
import base64
import datetime

diffdata = 'stablediff#'

@bot.callback_query_handler(
    is_chat=False,
    func=lambda call: call.data == CallbackData.stable_diffusion,
    service='stable_diffusion',
    is_subscription=True,
)
async def sd_callback_handler(call):
    """ Главная Stable Diffusion по callback
    """
    # Data
    msg, kb = await parse_stable_diffusion(call)
    # Send data
    try:
        await bot.edit_message_text(
            chat_id      = call.from_user.id,
            message_id   = call.message.message_id,
            text         = msg,
            reply_markup = kb
        )
    except Exception as e:
        await bot.send_message(
            chat_id      = call.from_user.id,
            text         = msg,
            reply_markup = kb
        )

    # Состояние
    await bot.set_state(call.from_user.id, SdState.active)

class SdState(StatesGroup):
    """ Состояния бота в Stable Diffusion
    """
    active = State()

async def parse_stable_diffusion(message):
    """ Главная Stable Diffusion
    """
    models = {
        'main': 'Stable Diffusion',
        'stable_core': 'Stable Diffusion Core',
        'sd3': 'Stable Diffusion 3',
        'sd3-turbo': 'Stable Diffusion 3 Turbo',
    }
    user = u.get()
    sd_config = await stable_diffusion_user_config(message.from_user.id)

    message_stable_greeting = 'stable_diffusion_greeting'

    kb = InlineKeyboardMarkup()
    new_models = [StableDiffusion.engine_core] + StableDiffusion.stable_three

    if cfg.get('stable_diffusion', 'engine') not in new_models:
        kb.row(
            InlineKeyboardButton(_('i_change_style'), callback_data=f'{diffdata}edit_style'),
            InlineKeyboardButton(_('i_change_sampler'), callback_data=f'{diffdata}edit_sampler'),
        ).row(
            InlineKeyboardButton(_('i_change_cfg_scale'), callback_data=f'{diffdata}edit_cfg_scale'),
            InlineKeyboardButton(_('i_change_step'), callback_data=f'{diffdata}edit_step'),
        )

    if cfg.get('stable_diffusion', 'engine') in new_models:
        message_stable_greeting = 'stable_diffusion_core_greeting'
        kb.row(
            InlineKeyboardButton(_('i_change_style'), callback_data=f'{diffdata}edit_style'),
            InlineKeyboardButton(_('i_change_aspect_ratio'), callback_data=f'{diffdata}edit_aspect_ratio'),
        )

    kb.row(
        InlineKeyboardButton(_('inline_back_to'), callback_data=CallbackData.user_home)
    )

    numerals_requests = _('numerals_requests')

    requests_price = {
        # text to image
        'tti':int(round(
            user.get('balance', 0) / cfg.getint('stable_diffusion', 'tti_price'), 0
        )),
        # image to image
        'iti': int(round(
            user.get('balance', 0) / cfg.getint('stable_diffusion', 'iti_price'), 0
        ))

    }

    sd_config['style_preset'] = _('dict_styles').get(str(sd_config['style_preset']))

    sd_config['model'] = models.get(cfg.get('stable_diffusion', 'engine'), ' Stable Diffusion')
    sd_config['request_count'] = 1
    sd_config['price_iti'] = cfg.get('stable_diffusion', 'iti_price')
    sd_config['price_tti'] = cfg.get('stable_diffusion', 'tti_price')

    sd_config['r1'] = Pluralize.declinate(requests_price['tti'], numerals_requests).word
    sd_config['r2'] = Pluralize.declinate(requests_price['iti'], numerals_requests).word

    sd_config['requests_tti'] = requests_price['tti']
    sd_config['requests_iti'] = requests_price['iti']

    ratios = _('dict_aspect_ratios')
    sd_config['ratio_description'] = ratios.get(sd_config.get('aspect_ratio'), ratios.get('1:1')).get('text')

    sd_config['aspect_ratio'] = sd_config['aspect_ratio']

    return _(message_stable_greeting).format(**sd_config), kb

async def stable_diffusion_user_config(user_id):
    """ Инициализирует базовую конфигурацию пользователя
        или возвращает существующую, если она была.

        Данные хранятся в Redis
    """
    default_config = {
        'style_preset': None,
        'steps': 50,
        'cfg_scale': 7,
        'sampler': 'DDPM',
        'aspect_ratio': '1:1',
    }

    model = cfg.get('stable_diffusion', 'engine')
    rkey_config = f'{user_id}_stable_{model}_diffusion_config'
    data_config = await cache.get(rkey_config.format(user_id))

    if not data_config:
        await cache.set(
            rkey_config,
            json.dumps(default_config)
        )
        data_config = json.dumps(default_config)

    return json.loads(data_config) or default_config

async def stable_diffusion_update_config(user_id, key, val):
    model = cfg.get('stable_diffusion', 'engine')
    rkey_config = f'{user_id}_stable_{model}_diffusion_config'
    data_config = await cache.get(rkey_config.format(user_id))
    data_config = json.loads(data_config)
    data_config[key] = val
    await cache.set(
        rkey_config.format(user_id),
        json.dumps(data_config)
    )

    return data_config

@bot.callback_query_handler(is_chat=False, func=lambda c: c.data.startswith('editstable#'))
async def stable_diffusion_edit_param(call):
    param = call.data.replace('editstable#', '').split('|')
    key, val = param[0], param[1]
    await stable_diffusion_update_config(call.from_user.id, key, val)
    # Data
    msg, kb = await parse_stable_diffusion(call)
    # Send data
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda c: c.data.startswith(diffdata))
async def stable_diffusion_edit_param(call):
    param = call.data.replace(diffdata, '')
    sd_config = await stable_diffusion_user_config(call.from_user.id)

    kb = {}
    msg = 'Test Mode'

    if param in ['edit_style']:
        msg = _('choose_stable_param_style_preset')
        presets = cfg.get('stable_diffusion', 'style_presets')
        for i in presets.split(','):
            name = _('dict_styles').get(i)
            if str(sd_config.get('style_preset')) == i:
                name = '✅ ' + name
            kb.update({
                name: {
                    'callback_data': 'editstable#style_preset|' + str(i)
                }
            })

    if param in ['edit_cfg_scale', 'edit_step']:
        await bot.set_state(call.from_user.id, EditStableParam.A1)
        async with bot.retrieve_data(call.from_user.id) as data:
            data['param'] = param

        descp = _('dict_config_params').get(param)
        msg = _('input_new_value_param').format(descp)

    if param in ['edit_sampler']:
        msg = _('choose_stable_param_sampler')
        presets = cfg.get('stable_diffusion', 'samplers')
        for i in presets.split(','):
            if str(sd_config.get('sampler')) == i:
                i = '✅ ' + i
            kb.update({
                i: {
                    'callback_data': 'editstable#sampler|' + str(i)
                }
            })

    if param in ['edit_aspect_ratio']:
        ratios = _('dict_aspect_ratios')
        msg = f"""{_('choose_stable_param_aspect_ratio')}\n\n{ratios.get(sd_config.get('aspect_ratio'), ratios.get('1:1')).get('text')}"""
        presets = cfg.get('stable_diffusion', 'aspect_ratios')
        for i in presets.split(','):
            cname = i
            if str(sd_config.get('aspect_ratio')) == i:
                i = '✅ ' + i
            kb.update({
                i: {
                    'callback_data': 'editstable#aspect_ratio|' + str(cname)
                }
            })

    kb.update({
        _('inline_back_to'): {
            'callback_data': CallbackData.stable_diffusion
        }
    })

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = BotKeyboard.smart(kb, row_width=2),
    )

@bot.message_handler(is_chat=False, state=EditStableParam.A1, content_types=['text'], is_subscription=True, stats='stable_edit_param')
async def stable_diffusion_save_params(message):
    """ Изменяет настройки Stable Diffusion
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        try:
            param = data['param'].replace('✅ ', '')
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
            await stable_diffusion_update_config(message.from_user.id, key, val)
            # Data
            msg, kb = await parse_stable_diffusion(message)
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

@bot.message_handler(is_chat=False, state=SdState.active, content_types=['photo', 'text'], is_subscription=True, continue_command='stable_diffusion', stats='stable_request')
async def stable_diffusion_message_handler(message):
    """ Обрабатывает запрос к Stable Diffusion
    """
    user = u.get()
    stable_errors = _('dict_stable_errors')

    user_subscribe = user['is_subscriber']

    lock = await get_lock(message.from_user.id)

    async with lock:
        # спорно, что это здесь находится, но ок
        balancer = BalancingKeys('stable_diffusion', 50)
        api_key = await balancer.get_available_key()

        service = StableDiffusion(api_key)
        sd_config = await stable_diffusion_user_config(message.from_user.id)

        mode = 'text-to-image'
        model = cfg.get('stable_diffusion', 'engine')

        prompt = message.text[:2048] if message.text else ''

        tokens_variants_price = cfg.getint('stable_diffusion', 'iti_price') if message.photo else cfg.getint('stable_diffusion', 'tti_price')

        init_image = None
        numerals_tokens = _('numerals_tokens')

        generate_redis_key = CacheData.stable_generation.format(message.from_user.id)
        generate = await cache.get(generate_redis_key)

        # мега спорно что это тоже теперь находится здесь
        if message.photo and service.engine_core == model:
            await bot.send_message(
                chat_id = message.from_user.id,
                text    = _('mode_image_to_image_not_support')
            )
            return

        if generate is not None:
            await bot.send_message(
                message.from_user.id,
                _('waiting_stable_generation')
            )
            return

        await cache.set(generate_redis_key, 1)
        await cache.expire(generate_redis_key, 30)

        # Если токены на балансе закончились, уведомляем
        if (
            user['balance'] < tokens_variants_price and
            cfg.getboolean('default', 'unlimited') is False and
            user['is_unlimited'] == False
        ):
            await exceed_limit(
                message.from_user.id,
                user['language_code'],
                (tokens_variants_price - user['balance']),
                key_string = 'remained_exceeded_limit',
                type = 'user'
            )

            await bot.delete_state(message.from_user.id)

            await cache.delete(CacheData.stable_generation.format(
                message.from_user.id
            ))

            return

        if message.photo:
            mode = 'image-to-image'
            image_info = await bot.get_file(message.photo[-1].file_id)
            init_image = await bot.download_file(image_info.file_path)
            prompt = message.caption if message.caption else ' '

        loading_text = await bot.send_message(
            message.from_user.id,
            _('waiting_stable')
        )

        await message_add_list(_('waiting_stable'), message.chat.id, loading_text.message_id, user['language_code'], 'stable')

        data = await service.image_create(
            text         = prompt,
            style_preset = sd_config.get('style_preset'),
            mode         = mode,
            steps        = sd_config.get('steps'),
            cfg_scale    = sd_config.get('cfg_scale'),
            sampler      = sd_config.get('sampler'),
            aspect_ratio = sd_config.get('aspect_ratio'),
            init_image   = init_image
        )

        await message_remove_list(message.chat.id, loading_text.message_id, user['language_code'], 'stable')

        await balancer.decrease_connection(api_key)

        await bot.delete_message(message.from_user.id, loading_text.message_id)

        bot_info = await bot.get_me()

        stable_params = _('stable_image_params').format(**{
            "style_preset": _('dict_styles').get(str(sd_config.get('style_preset'))).lower(),
            "sampler":      sd_config.get('sampler'),
            "cfg_scale":    sd_config.get('cfg_scale'),
            "step":         sd_config.get('steps'),
        })

        text_for_caption = escape_html(prompt)
        description = _('stable_image_additional_info').format(**{
            "request":      escape_html(prompt) if len(prompt) < 800 else text_for_caption[0:850] + '...',
            "name":         bot_info.first_name,
            "username":     bot_info.username,
            "model":        'Stable Diffusion',
            "params":       '' if service.engine_core == model or model in service.stable_three else stable_params
        })

        anythin_else_kb = BotKeyboard.smart({
            _('inline_dalle_generate'): {"callback_data": CallbackData.stable_diffusion},
            _('inline_back_to_main_menu'): {"callback_data": CallbackData.user_home}
        })

        remaining_balance = (user['balance'] - tokens_variants_price)
        # При безлимитном режиме баланс остаётся тем же
        if cfg.getboolean('default', 'unlimited') or user['is_unlimited']:
            remaining_balance = user['balance']

        string_variants_price = Pluralize.declinate(tokens_variants_price, numerals_tokens)
        string_remaining_balance = Pluralize.declinate(remaining_balance, numerals_tokens, type=5)

        media_variants = []
        try:
            err_msg = _('error_request')
            new_models = [StableDiffusion.engine_core] + StableDiffusion.stable_three

            if not api_key:
                err_msg += _('error_request_for_admin').format(_('error_key_not_exist'))
                raise Exception(err_msg)

            if cfg.get('stable_diffusion', 'engine') not in new_models and data.get('artifacts'):
                raise Exception(
                   _('dict_stable_errors').get(data.get('name')) or _('dict_stable_errors').get('None')
                )

            if cfg.get('stable_diffusion', 'engine') in new_models and data.get('errors'):
                logging.warning(data.get('errors'))
                raise Exception(
                   f"{stable_errors.get(data.get('name'), stable_errors.get('rate_limit_exceeded'))}\n\n {','.join(data.get('errors', 'Error'))}" or _('dict_stable_errors').get('None', 'Undefined error')
                )

            artifacts = None
            stable_image = None


            if cfg.get('stable_diffusion', 'engine') in new_models:
                artifacts = [{'base64': data.get('image')}]
            else:
                artifact = data.get('artifacts')

            for k, v in enumerate(artifacts):
                caption = description if k == 0 else ''
                stable_image = base64.b64decode(v["base64"])
                media_variants.append(
                    InputMediaPhoto(
                        stable_image,
                        caption=caption, parse_mode='HTML'
                    )
                )
            await bot.send_media_group(
                chat_id             = message.chat.id,
                media               = media_variants,
                reply_to_message_id = message.id
            )

            # Бля понимаю что try в try это пиздец, но...
            try:
                await bot.send_document(
                    message.chat.id,
                    (
                        f'stable_diffusion_{datetime.datetime.now()}.jpeg', # TO-DO переделать под output_format,
                        stable_image
                    ),
                    caption = _('original_image_file')
                )
            except Exception as e:
                logging.warning(e)

            await db.create_request(
                user['id'],
                0,
                'stable_diffusion',
                json.dumps(prompt),
                # json.dumps(data['artifacts']),
                '-',
                total_tokens = tokens_variants_price,
                unlimited    = int(cfg.getboolean('default', 'unlimited')) or user['is_unlimited'],
                is_sub = user_subscribe
            )

            await bot.send_message(
                message.from_user.id,
                text = _('stable_anything_else').format(**{
                    "amount_token": tokens_variants_price,
                    "p1":           string_variants_price.word,
                    "balance":      remaining_balance,
                    "p2":           string_remaining_balance.word,
                }),
                reply_markup = anythin_else_kb
            )
        except Exception as e:
            logging.warning(e)
            await bot.send_message(
                message.from_user.id,
                text = str(e),
                reply_markup = anythin_else_kb
            )
        # Удаляем key для снятия ограничений
        await cache.delete(generate_redis_key)

@bot.message_handler(is_chat=False, commands=['stable'], service='stable_diffusion', is_subscription=True, stats='stable_home')
async def sd_command_handler(message):
    """ Главная Stable Diffusion по команде /stable
    """
    # Data
    msg, kb = await parse_stable_diffusion(message)

    # Send data
    await bot.send_message(
        message.from_user.id,
        text         = msg,
        reply_markup = kb
    )

    # Состояние
    await bot.set_state(message.from_user.id, SdState.active)
