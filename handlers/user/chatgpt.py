# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config as cfg, _
from utils.openai import chatgpt
from states.states import BotState, CreateDialog
from keyboards.inline import BotKeyboard
from telebot.formatting import escape_markdown
from telebot.util import extract_arguments
from utils.strings import CallbackData, CacheData
from telebot.asyncio_handler_backends import ContinueHandling
from utils.functions import openai_chatgpt_models
from utils.configurable import get_lock

import json
import asyncio

@bot.message_handler(
    is_chat=False,
    state=BotState.gpt_chat,
    service='gpt',
    control_gpt=['reply_end_dialog', '/end'],
    is_subscription=True
)
async def gpt_clear_history_chat_handler(message, data):
    """ Завершает текущий диалог с ChatGPT
    """
    user = data['user']
    async with bot.retrieve_data(message.from_user.id) as data:
        dialog = json.loads(data['dialog'])
        end = await bot.send_message(
            chat_id=message.from_user.id,
            text=_('dialog_is_end').format(
                dialog['title']
            ),
            reply_markup=BotKeyboard.remove_reply()
        )
        # await bot.delete_message(
        #     chat_id    = message.from_user.id,
        #     message_id = end.message_id
        # )

        kb = await BotKeyboard.create_dialog_chatgpt(user)
        await bot.send_message(
            chat_id=message.from_user.id,
            text=_('chatgpt_dialogs'),
            reply_markup=kb
        )

    await bot.delete_state(message.from_user.id)

@bot.message_handler(
    is_chat=False,
    state=BotState.gpt_chat,
    control_gpt=['reply_dialog_clear', '/clear'],
    service='gpt',
    is_subscription=True
)
async def gpt_clear_history_chat_handler(message, data):
    """ Очищает историю текущего диалога с ChatGPT
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        dialog = json.loads(data['dialog'])
        await db.history_clear(dialog_id=dialog['id'])
        await bot.send_message(
            chat_id=message.from_user.id,
            text=_('dialog_cleaned')
        )

@bot.message_handler(is_chat=False, state=BotState.gpt_chat, service='gpt', is_subscription=True, content_types=['video', 'sticker', 'document', 'video_note', 'audio', 'location', 'contact', 'pinned_message', 'animation'])
async def gpt_dialog_not_supported_content(message, data):
    await bot.send_message(
        chat_id  = message.from_user.id,
        text     = _('gpt_not_supported_content')
    )

@bot.message_handler(is_chat=False, state=BotState.gpt_chat, service='gpt', is_subscription=True, continue_command='gpt', content_types=['text', 'voice', 'photo'])
async def gpt_dialog_handler(message, data):
    """ Обработка активного диалога с ChatGPT

        Отвечает на каждое сообщение, до /clear, /end
    """
    user = data['user']
    message_edit_id = None
    image = None

    # if message.text in _('commands').keys():
    #     async with bot.retrieve_data(message.from_user.id) as data:
    #             dialog = json.loads(data['dialog'])
    #             end = await bot.send_message(
    #                 chat_id=message.from_user.id,
    #                 text=_('dialog_is_end').format(
    #                     dialog['title']
    #                 ),
    #                 reply_markup=BotKeyboard.remove_reply()
    #             )
    #     await bot.delete_state(message.from_user.id)
    #
    #     return ContinueHandling()

    if message.content_type == 'photo':
        image = message.photo[-1]
        image = await bot.get_file(image.file_id)
        image = await bot.download_file(image.file_path)
        message.text = message.caption if message.caption else _('describe_photo')

    if (
        message.content_type == 'voice' and
        cfg.getboolean('openai', 'speech') is False
    ):
        await bot.send_message(
            chat_id = message.from_user.id,
            text    = _('dialog_speech_disabled')
        )
        return

    if message.content_type == 'voice' and message.voice.duration > 301:
        await bot.send_message(
            chat_id = message.from_user.id,
            text    = _('dialog_limit_voice')
        )
        return

    if message.content_type == 'voice':
        notify = await bot.send_message(
            chat_id = message.from_user.id,
            text    = _('dialog_speech_decoding')
        )
        message_edit_id = notify.message_id
        message.text = '/gpt'

    gpt_lock_key = CacheData.chatgpt_generation.format(message.from_user.id)
    gpt_lock = await cache.get(gpt_lock_key)

    if gpt_lock:
        await bot.send_message(
            chat_id = message.from_user.id,
            text    = _('gpt_locked_request')
        )
        return

    async with bot.retrieve_data(message.from_user.id) as data:
        try:
            lock = await get_lock(message.from_user.id)
            async with lock:
                await cache.set(gpt_lock_key, 0)
                await cache.expire(gpt_lock_key, 30)
                await chatgpt.chatgpt(
                    user,
                    {
                        'message_id': message.message_id,
                        'from_user_id': message.from_user.id,
                        'chat_id': message.chat.id,
                        'text': message.text,
                        'content_type': message.content_type,
                        'voice': message.voice,
                        'image': image
                    },
                    dialog = json.loads(data['dialog']),
                    message_edit_id = message_edit_id
                )

        except Exception as e:
            print(e)

    await cache.delete(gpt_lock_key)

@bot.callback_query_handler(is_chat=False, state=BotState.gpt_chat, func=lambda call: call.data == CallbackData.dialogs_chatgpt, service='gpt')
async def callback_handler(call, data):
    """ Диалоги с ChatGPT

        Выход из диалога с состоянием
    """
    user = data['user']

    async with bot.retrieve_data(call.from_user.id) as data:
            dialog = json.loads(data['dialog'])
            await bot.delete_message(
                chat_id=call.from_user.id,
                message_id=call.message.message_id,
            )
            end = await bot.send_message(
                chat_id=message.from_user.id,
                text=_('dialog_is_end').format(
                    dialog['title']
                ),
                reply_markup=BotKeyboard.remove_reply()
            )

    await bot.delete_state(call.from_user.id)

    await bot.send_message(
        chat_id=call.from_user.id,
        text=_('chatgpt_dialogs'),
        parse_mode="Markdown",
        reply_markup=await BotKeyboard.create_dialog_chatgpt(user)
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.dialogs_chatgpt, service='gpt', stats='chatgpt_dialogs', is_subscription=True)
async def callback_handler(call, data):
    """ Диалоги с ChatGPT
    """
    await bot.delete_state(call.from_user.id)
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=_('chatgpt_dialogs'),
        parse_mode="Markdown",
        reply_markup=await BotKeyboard.create_dialog_chatgpt(data['user'])
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.start_chatgpt_dialog), service='gpt',  stats='chatgpt', is_subscription=True)
async def callback_handler(call, data):
    """ Открывает диалог с ChatGPT
    """
    user = data['user']

    # Начинает диалог с ChatGPT
    dialog_param = call.data.replace(CallbackData.start_chatgpt_dialog, "")
    dialog_param = dialog_param.split("#")

    dialog_id = dialog_param[0]
    dialog = await db.get_dialog({'id': dialog_id})

    if not dialog:
        await bot.answer_callback_query (
            call.id,
            _('chatgpt_dialog_not_found')
        )
        return

    kb = {}

    dict_speech_status = _('dict_speech_status_simple')
    dict_save_history = _('dict_save_history')
    dict_animation_text = _('dict_animation_text')
    dict_inline_save_history = _('dict_inline_save_history')
    dict_inline_billing_history = _('dict_view_billing_information')

    sh = await chatgpt.save_history(user['id'], dialog[0]['id'])

    try:
        if dialog_param[1].startswith('sh_'):
            sh = dialog_param[1].replace('sh_', '')
            sh = 1 if int(sh) == 0 else 0
            await chatgpt.save_history(user['id'], dialog[0]['id'], sh, True)

        if dialog_param[1].startswith('bi_'):
            bi = dialog_param[1].replace('bi_', '')
            user['billing_information'] = 1 if int(bi) == 0 else 0
            await db.update_user(
                user['telegram_id'],
                {'billing_information': user['billing_information']}
            )
    except Exception as e:
        pass

    kb.update({
        # _('inline_export_dialog'): {
        #     "callback_data": 'exp'
        # },
        dict_inline_save_history[sh]: {
            "callback_data": CallbackData.start_chatgpt_dialog + f"{dialog[0]['id']}#sh_{sh}"
        },
        dict_inline_billing_history[user['billing_information']]: {
            "callback_data": CallbackData.start_chatgpt_dialog + f"{dialog[0]['id']}#bi_{user['billing_information']}"
        },

    })

    if user['role'] in ['admin', 'demo']:
        kb.update({
            _('inline_get_edit'): {'callback_data': CallbackData.admin_chatgpt_dialog_view+str(dialog[0]['id'])}
        })

    kb.update({
        _('inline_back_to_dialogs_chatgpt'): {
            "callback_data": CallbackData.dialogs_chatgpt
        }
    })

    str_view_dialog = 'chatgpt_system_greeting' if dialog[0]['is_system'] == 1 else 'chatgpt_greeting'

    msg_chatgpt_greeting = _(str_view_dialog).format(**{
        'name': dialog[0]['title'],
        'role': dialog[0]['role'],
        'history': dict_save_history[sh],
        'model': dialog[0]['model'],
        'speech_status': dict_speech_status[int(cfg.getboolean('openai', 'speech'))],
    })

    kb = BotKeyboard.smart(kb)
    welcome_message = dialog[0]['welcome_message']

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=msg_chatgpt_greeting,
        parse_mode="Markdown",
        reply_markup=None if welcome_message not in ['-', None] else kb,
    )

    if welcome_message not in ['-', None]:
        await asyncio.sleep(0.25)
        await bot.send_message(
            chat_id=call.message.chat.id,
            text=dialog[0]['welcome_message'],
            parse_mode="HTML",
            reply_markup=kb,
        )

    # Предупреждаем о перерасходе токенов
    # if '-vision-' in dialog[0]['model']:
    #     await bot.send_message(
    #         chat_id=call.message.chat.id,
    #         text=_('only_image_with_propmpt_dialog'),
    #         parse_mode="Markdown",
    #         reply_markup=await BotKeyboard.start_gpt_dialog(user)
    #     )

    await bot.set_state(call.from_user.id, BotState.gpt_chat)

    async with bot.retrieve_data(call.from_user.id) as data:
        data['dialog'] = json.dumps(
            dialog[0],
            indent=4,
            sort_keys=True,
            default=str
        )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.create_dialog_chatgpt, service='gpt', is_subscription=True)
async def callback_handler(call, data):
    """ Создание диалога с chatgpt
    """
    get_dialogs_count = await db.get_count(
        table="dialogs",
        q={
            "user_id": data['user']['id'],
            "is_active": 1,
            "is_system": 0
        }
    )

    if get_dialogs_count >= cfg.getint('openai', 'max_custom_gpt_dialogs'):
        # Достигнуто максимальное кол-во диалогов
        await bot.answer_callback_query(
            call.id,
            text=_('warning_limit_create_dialogs'),
            show_alert=True
        )
        return

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=_('create_dialog_step_1'),
        parse_mode="Markdown",
        reply_markup=BotKeyboard.back_to_create_dialog_chatgpt()
    )

    await bot.set_state(call.from_user.id, CreateDialog.A1)

@bot.message_handler(is_chat=False, state=CreateDialog.A1, service='gpt', is_subscription=True)
async def bot_create_chatgpt_dialog(message, data):
    """ Ввод названия диалога
    """
    user = data['user']

    async with bot.retrieve_data(message.from_user.id) as data:
        if len(message.text) > 60:
            await bot.send_message(
                chat_id=message.chat.id,
                text=_('gpt_error_dialog_name'),
                parse_mode="Markdown",
                reply_markup=BotKeyboard.back_to_create_dialog_chatgpt()
            )
            return

        data['name'] = message.text

        await bot.send_message(
            chat_id=message.chat.id,
            text=_('create_dialog_step_2'),
            parse_mode="Markdown",
            reply_markup=BotKeyboard.gpt_models()
        )

    # TWO STEP
    await bot.set_state(message.from_user.id, CreateDialog.A2)

@bot.message_handler(is_chat=False, state=CreateDialog.A2, service='gpt', is_subscription=True, continue_command='delete_reply_keyboard')
async def dialog_gpt(message, data):
    """ Модели ChatGPT
    """
    user = data['user']
    models = list(openai_chatgpt_models().keys())

    async with bot.retrieve_data(message.from_user.id) as data:
        if message.text not in models:
            await bot.send_message(
                chat_id=message.chat.id,
                text=_('gpt_error_dialog_model'),
                parse_mode="Markdown"
            )
            return

        data['model'] = message.text

        await bot.send_message(
            chat_id = message.from_user.id,
            text = _('dialog_model_selected').format(message.text),
            reply_markup = BotKeyboard.remove_reply()
        )
        await bot.send_message(
            chat_id=message.chat.id,
            text=_('create_dialog_step_3'),
            parse_mode="Markdown",
            reply_markup=BotKeyboard.back_to_create_dialog_chatgpt()
        )

    # TWO STEP
    await bot.set_state(message.from_user.id, CreateDialog.A3)

@bot.message_handler(is_chat=False, state=CreateDialog.A3, service='gpt', is_subscription=True)
async def bot_inpute_role_chatgpt_dialog(message, data):
    """ Ввод стиля (роли) диалога
    """
    user = data['user']

    async with bot.retrieve_data(message.from_user.id) as data:
        if len(message.text) < 4 or len(message.text) > 2048:
            await bot.send_message(
                chat_id=message.chat.id,
                text=_('gpt_error_dialog_role'),
                parse_mode="Markdown",
                reply_markup=BotKeyboard.back_to_create_dialog_chatgpt()
            )
            return
        try:
            # Создание дилалога
            dialog_id = await db.create_dialog(
                user['id'],
                data['name'],
                role=message.text,
                top_p = cfg.getint('openai', 'top_p'),
                max_tokens = cfg.getint('openai', 'max_tokens'),
                temperature = cfg.getfloat('openai', 'temperature'),
                presence_penalty = cfg.getfloat('openai', 'presence_penalty'),
                frequency_penalty = cfg.getfloat('openai', 'frequency_penalty'),
                count_history_messages = cfg.getfloat('openai', 'max_history_message'),
                model = data['model']
            )
        except Exception as e:
            print(e)

        msg = _('dialog_created').format(**{
            "name": escape_markdown(data['name'])
        })
        await bot.send_message(
            chat_id      = message.chat.id,
            text         = msg,
            parse_mode   = "Markdown",
            reply_markup = BotKeyboard.next_new_dialog(dialog_id)
        )

    await bot.delete_state(message.from_user.id)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.deactivate_chatgpt_dialog), service='gpt', is_subscription=True)
async def callback_handler(call, data):
    """ Удаление диалога с ChatGPT
    """
    dialog_id = call.data.replace(CallbackData.deactivate_chatgpt_dialog, "")

    await db.update_dialog(
        data['user']['id'],
        dialog_id,
        {"is_active": 0, 'title': '', 'role': ''}
    )
    await db.history_clear(dialog_id)

    await bot.answer_callback_query (
        call.id,
        text=_(
        'chatgpt_dialog_success_deactivate')
    )

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=_('chatgpt_dialogs'),
        parse_mode="Markdown",
        reply_markup=await BotKeyboard.create_dialog_chatgpt(data['user'])
    )


@bot.message_handler(is_chat=False, commands=['gpt'], service='gpt',  stats='chatgpt_dialogs', is_subscription=True)
async def gpt_command_handler(message, data):
    """ Открывает ChatGPT диалоги
        если не был указан запрос /gpt запрос
    """
    text = message.text.replace('/gpt ', '').replace('/gpt', '')
    if len(text) < 4:
        kb = await BotKeyboard.create_dialog_chatgpt(data['user'])
        await bot.reply_to(
            message,
            text=_('chatgpt_dialogs'),
            reply_markup=kb
        )
        return

    lock = await get_lock(message.from_user.id)
    async with lock:
        await chatgpt.chatgpt(
            data['user'],
            {
                'message_id': message.message_id,
                'from_user_id': message.from_user.id,
                'chat_id': message.chat.id,
                'text': message.text
            }
        )
