# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

import openai
import telegram
import json
import re
import asyncio
import aiohttp
import base64
import io

from loader import bot, cache, db, config, _
from telebot.util import smart_split, escape
from telebot.formatting import escape_markdown, escape_html
from keyboards.inline import BotKeyboard
from utils.openai.whisper import recognize_speech
from utils.openai.chat_completion import chat_completion
from utils.texts import Pluralize, split_text
from utils.limits import exceed_limit
from utils.strings import CallbackData, CacheData
from utils.balancing import BalancingKeys
from utils.subscriptions import check_subscription
from utils.message_loader import message_add_list, message_remove_list
from utils.functions import openai_chatgpt_models
from utils.logging import logging

async def save_history(user_id, dialog_id, new_param: int = 0, save: bool = False) -> int:
    """ Сохраняет/не сохраняет историю диалогa
    """
    param = await cache.get(
        CacheData.dialog_save_history.format(user_id, dialog_id)
    )

    if save or param is None:
        param = new_param
        await cache.set(
            CacheData.dialog_save_history.format(user_id, dialog_id),
            new_param
        )

    return int(param)

async def chatgpt(
    user:            json,
    message:         json,
    user_type:       str = 'user',
    dialog:          int = 0,
    state:           bool = True,
    inline_mode:     bool = False,
    message_edit_id: int = None,
):
    """ Обрабатывает пользовательский запрос к ChatGPT

        :user:      json пользователь
        :message:   json сообщение
        :user_type: str    тип юзера [user или chat]
        :dialog:    dict   данные о диалоге
    """
    multiplier = openai_chatgpt_models()
    print(multiplier)
    telegram_id = message.get('from_user_id') if user_type == 'user' else message.get('chat_id')

    user_subscribe = user['is_subscriber']

    dialog_id = 0
    dialog_keyboard = None

    request_type = 'text'
    prompt = message.get('text', '/gpt').replace("/gpt", "")
    messages = [] # роль, ~история, промпт

    if message.get('content_type') == 'voice':
        request_type = 'voice_to_text'
        voice = message.get('voice')
        file_info = await bot.get_file(voice.file_id)
        audio = await bot.download_file(file_info.file_path)
        speech_text = await recognize_speech(audio, file_info.file_path)
        prompt = speech_text

    model = config.get('openai', 'model')
    animation = config.getboolean('openai', 'animation_text')

    sh = config.getboolean('openai', 'save_history')
    count_history_messages = config.getint('openai', 'max_history_message')

    completion = config['openai']['default_answer']
    chatgpt_role = config['openai']['default_role']

    top_p = config.getint('openai', 'top_p')
    max_tokens = None
    # max_tokens = config.getint('openai', 'max_tokens')
    temperature = config.getfloat('openai', 'temperature')
    presence_penalty = config.getfloat('openai', 'presence_penalty')
    frequency_penalty = config.getfloat('openai', 'frequency_penalty')

    string_dialog_clear = _('inline_dialog_clear')
    string_dialog_end = _('end_dialog')

    # Если диалог вызывается не через команду
    # то в dialog попадаёт словарь с данными о диалоге
    if type(dialog) == dict:
        dialog_keyboard = BotKeyboard.gpt_dialog()
        dialog_id = dialog['id']
        model = dialog['model']
        chatgpt_role = dialog['role']
        top_p = dialog['top_p']
        max_tokens = None
        # max_tokens = dialog['max_tokens']
        temperature = dialog['temperature']
        presence_penalty = dialog['presence_penalty']
        frequency_penalty = dialog['frequency_penalty']
        animation = bool(dialog['animation_text'])
        sh = bool(await save_history(user['id'], dialog_id))
        count_history_messages = dialog['count_history_messages']


    if 'vision' not in model and message.get('image'):
        model = 'gpt-4-turbo-2024-04-09'

    if model.startswith('gpt-4') and user['balance'] < config.getint('openai', 'gpt4_min_balance'):
        await bot.send_message(
            chat_id=message.get('from_user_id'),
            text=_('gpt4_min_balance').format(**{
                'gpt4_min_balance': config.getint('openai', 'gpt4_min_balance'),
                'model': model,
            }),
            reply_markup=BotKeyboard.smart({
                _('inline_shop'): {'callback_data': CallbackData.home_shop},
                _('inline_refferal_program'): {'callback_data': CallbackData.refferal_program}
            })
        )
        return

    unlimited_models = config.get('openai', 'unlimited_models').split(",")
    # Безлимит на gpt-3.5... за подписку на канал
    if (
        config.getboolean('subscribe', 'unlim_gpt35turbo') and
        user_subscribe == 0 and
        user_type == 'user' and
        model in unlimited_models and
        await check_subscription(user, msg = {'from_user_id': message.get('from_user_id')}, action = False)
    ):
        user['is_unlimited'] = 1

    if (
        user_subscribe and
        await cache.get(f'unlimsub_{user["id"]}') and
        model in unlimited_models
    ):
        user['is_unlimited'] = 1

    # Если на балансе не хватает токенов - уведомляем
    # Обнуляем состояние текущего диалога
    if (
        user['balance'] <= 0 and
        config.getboolean('default', 'unlimited') is False and
        user['is_unlimited'] == False
    ):
        if dialog_id > 0:
            await bot.send_message(
                chat_id=message.get('from_user_id'),
                text=_('dialog_is_end').format(
                    dialog['title']
                ),
                reply_markup=BotKeyboard.remove_reply()
            )
        await exceed_limit(
            telegram_id,
            user['language_code'],
            key_string = 'exceeded_limit' if user_type == 'user' else 'exceeded_limit_chat',
            type = user_type,
            model = model
        )

        if user_type == 'user':
            await bot.delete_state(message.get('from_user_id'))

        return None

    # Добавляем историю переписки (если предусмотрено диалогом)
    # Доступно только для диалогов, вызываемых через меню
    if dialog_id > 0 and sh and inline_mode == False:
        chatgpt_requests = await db.get_requests(
            user['id'],
            dialog_id,
            limit=count_history_messages
        )

        if chatgpt_requests is not None:
            for r in chatgpt_requests:
                messages.extend([
                    {"role": "user", "content": r['message']},
                    {"role": "assistant", "content": r['answer']},
                ])
                # делаем реверс, тк из базы идёт DESCENDING с лимитом
                messages = messages[::-1]

    # Не поддерживается
    # if (
    #     type(dialog) == dict and
    #     not dialog['is_system'] and
    #     'vision' not in model and
    #     message.get('image')
    # ):
    #     await bot.send_message(
    #         chat_id             = message.get('chat_id'),
    #         text                = _('vision_not_supporting').format(model),
    #         reply_to_message_id = message.get('message_id'),
    #     )
    #     return

    # Добавляем промпт последним
    if model in ['gpt-4-turbo-2024-04-09', 'gpt-4-vision-preview']:
        max_tokens = 4096

    if model in ['gpt-4-turbo-2024-04-09', 'gpt-4-vision-preview'] and message.get('image'):
        request_type = 'image_to_text'
        b64image = base64.b64encode(message.get('image')).decode('utf-8')
        text = [
            {
                "type": "text",
                "text": prompt or 'ChatGPT'
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64image}"
                }
            }
        ]
        messages.append({"role": "user", "content": text})

    else:
        messages.append({"role": "user", "content": prompt})
    #
    # ur = await read_url('https://zverev.io/')
    # if ur:
    #     messages.append({"role": "user", "content": '[https://taroznanie.ru/ - html code]' + remove_script_tags(ur)})
    #     # return

    # Иницализируем класс распределения токенов
    balancer = BalancingKeys('openai', 50)
    gpt = None

    try:
        if not prompt:
            raise Exception('Prompt undefined')

        if user['role'] in ['admin'] and prompt == '!call_error':
            raise Exception('Call error')

        if message_edit_id:
            await bot.delete_message(
                chat_id    = message.get('chat_id'),
                message_id = message_edit_id
            )

        if inline_mode == False:
            loader_text = f'🎙 {prompt}' if request_type.startswith('voice_to_text') else _('chatgpt_typing')
            gpt = await bot.send_message(
                chat_id             = message.get('chat_id'),
                text                = loader_text,
                reply_to_message_id = message.get('message_id'),
            )
            if user_type == 'user':
                await message_add_list(loader_text, message.get('chat_id'), gpt.message_id, user['language_code'], 'chatgpt')

        error_request_count = 0
        completion, usage, errors = None, None, None
        while True:
            # Берём ключ с наименьшим кол-вом соединений
            api_key = await balancer.get_available_key()

            if not api_key:
                raise Exception(_('error_key_not_exist'))

            # Отправляем запрос в OpenAi
            completion, usage, errors = await chat_completion(
                api_key           = api_key,
                model             = model,
                role              = chatgpt_role,
                prompt            = messages,
                top_p             = top_p,
                temperature       = temperature,
                presence_penalty  = presence_penalty,
                frequency_penalty = frequency_penalty,
                max_tokens        = max_tokens,
            )
            original_answer = completion

            # Освобождаем соединение для балансировщика
            await balancer.decrease_connection(api_key)

            if len(errors) > 0 and 'overloaded' in errors[1]:
                await asyncio.sleep(1.5)
                continue

            if len(errors) > 0 and errors[0] in ['AUTH', 'RATE_LIMIT', 'PERMISSION']:
                await balancer.delete(api_key)
                await db.update_key(api_key, {
                    'status': 'inactive',
                    'reason': f'{errors[0]}: {errors[1]}'
                })
                continue

            if len(errors) == 0:
                await message_remove_list(message.get('chat_id'), gpt.message_id, user['language_code'], 'chatgpt')
                break

            if len(errors) > 0 and error_request_count < 2:
                error_request_count += 1
                continue

            # Если есть ошибка, выходим
            if len(errors) > 0 and error_request_count >= 2:
                TYPE_ERROR = errors[0]
                DESC_ERROR = errors[1]
                # TASK: вывести уведомлене о загрузке openai, если будет ответ overloaded

                if TYPE_ERROR in ["AUTH", "PERMISSION", "RATE_LIMIT"]:
                    # Уведомляем админа и деактивируем ключ
                    await balancer.delete(api_key)
                    await db.update_key(api_key, {
                        'status': 'inactive',
                        'reason': f'{TYPE_ERROR}: {DESC_ERROR}'
                    })

                await message_remove_list(message.get('chat_id'), gpt.message_id, user['language_code'], 'chatgpt')

                logging.warning(f"{TYPE_ERROR}: {DESC_ERROR}")

                raise Exception(f"{TYPE_ERROR} | {DESC_ERROR}")

        # Список с числительными для плюрализации
        numerals_tokens = _('numerals_tokens')

        usage['total_tokens'] = int(usage['total_tokens'] * multiplier.get(model, 1))

        # Считаем оставшееся кол-во токенов
        openai_user_balance = (user['balance'] - usage['total_tokens'])

        # Если включен безлимитный режим, токены не расходуются
        if config.getboolean('default', 'unlimited') or user['is_unlimited']:
            openai_user_balance = user['balance']

        # Баланс не может быть меньше 0. В базе MySQL триггер
        # при балансе < 0 автоматически ставит 0
        if openai_user_balance < 0:
            openai_user_balance = 0

        # Отправляем ответ чату
        if user_type == 'chat':
            await bot.delete_message(
                message_id=gpt.message_id,
                chat_id=telegram_id
            )
            await bot.send_message(
                chat_id             = message.get('chat_id'),
                text                = str(original_answer),
                reply_to_message_id = message.get('message_id'),
            )

        usage['total_tokens'] = config.getint('openai', 'added_value_gpt') + usage['total_tokens']
        cfg_unlim = int(config.getboolean('default', 'unlimited'))

        if message.get('content_type') == 'voice' and len(prompt) > 5:
            usage['total_tokens'] = usage['total_tokens'] + config.getint('openai', 'added_value_speech')

        if user_type == 'user':
            # Отправка сообщения без анимации
            if animation is False:
                # Удаляем
                await bot.delete_message(
                    message_id=gpt.message_id,
                    chat_id=telegram_id
                )

                split_msg = smart_split(str(original_answer))

                for m in split_msg:
                    try:
                        gpt = await bot.send_message(
                            chat_id=telegram_id,
                            # message_id=gpt.message_id,
                            text=str(m),
                            reply_markup=dialog_keyboard
                        )
                    except Exception as e:
                        # В случае если OpenAi отправил некорректный Markdown
                        gpt = await bot.send_message(
                            text         = escape_html(m),
                            chat_id      = telegram_id,
                            parse_mode   = 'HTML',
                            reply_markup = dialog_keyboard
                        )
                        logging.warning(e)

                # Если у пользователя включена опция,
                # которая показывает стоимость запроса
                # добавляем её к сообщению

            if animation:
                # Разбиваем сообщение на валидные markdown строки (для анимации)
                chatgpt_answer = smart_split(str(original_answer), 156)

                msg = chatgpt_answer[0]
                last_message = msg

                if len(chatgpt_answer) >= 1:
                    chatgpt_answer.pop(0)

                gpt = await bot.edit_message_text(
                    message_id = gpt.message_id,
                    text       = msg,
                    chat_id    = telegram_id,
                    parse_mode = None
                )

                for answer in chatgpt_answer:
                    msg += answer

                    if msg == answer:
                        continue

                    try:
                        gpt = await bot.edit_message_text(
                            message_id = gpt.message_id,
                            chat_id    = telegram_id,
                            text       = msg,
                            parse_mode = "HTML"
                        )
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logging.warning(e)

            if (
                user['is_unlimited'] == 0 and
                user['billing_information']
            ):
                original_answer = _(
                    'chatgpt_tokens_usage'
                ).format(**{
                    "amount_token": usage['total_tokens'],
                    "p1": Pluralize.declinate(usage['total_tokens'], numerals_tokens).word,
                    "balance": openai_user_balance,
                    "p2": Pluralize.declinate(openai_user_balance, numerals_tokens, type=5).word,
                })

                # Информируем о безлимитном режиме
                if config.getboolean('default', 'unlimited'):
                    original_answer += _('unlimited_mode')

                await bot.send_message(
                    text         = original_answer,
                    chat_id      = telegram_id,
                    reply_markup = dialog_keyboard
                )
        await db.create_request(
            user['id'],
            dialog_id,
            'chatgpt',
            prompt,
            completion,
            request_type = request_type,
            prompt_tokens = usage['prompt_tokens'],
            completion_tokens = usage['completion_tokens'],
            total_tokens = usage['total_tokens'],
            unlimited = cfg_unlim if cfg_unlim else user['is_unlimited'],
            is_sub = user_subscribe
        )
    except Exception as e:
        # Удаляем ключ (если )
        if gpt:
            await message_remove_list(message.get('chat_id'), gpt.message_id, user['language_code'], 'chatgpt')

        if dialog != 0:
            # Завершаем диалог
            async with bot.retrieve_data(message.get('from_user_id')) as data:
                dialog = json.loads(data['dialog'])
                await bot.send_message(
                    chat_id = message.get('from_user_id'),
                    text = _('dialog_is_end').format(
                        dialog['title']
                    ),
                    reply_markup = BotKeyboard.remove_reply()
                )

        # Отправляем информацию об ошибке
        error_request_msg = _('error_request')
        error_request_msg += _('error_request_for_admin').format(
            escape_markdown(str(e)[:1024])
        )

        await bot.send_message(
            chat_id             = message.get('chat_id'),
            text                = error_request_msg,
            reply_to_message_id = message.get('message_id'),
            reply_markup        = BotKeyboard.smart({
                _('inline_back_to_dialogs_chatgpt'): {'callback_data': CallbackData.dialogs_chatgpt}
            }),
        )

        logging.warning(f"{message.get('chat_id')} {e}")

        await bot.delete_state(message.get('from_user_id'))
