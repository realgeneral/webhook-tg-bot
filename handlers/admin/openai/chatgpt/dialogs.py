# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u
from languages.language import lang_variants
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from states.states import AdminChatGpt
from telebot.formatting import escape_markdown
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.functions import openai_chatgpt_models

async def parse_chatgpt_dialogs():
    """ Главное меню системных диалогов ChatGPT
    """
    dialogs = await db.get_dialog({'is_system': 1, 'is_active': 1})

    msg = _('admin_chatgpt_dialogs')
    kb = []

    for d in dialogs:
        # name = d['title'] + ' ' + _('icon', d['language_code'])
        # kb[name] = {'callback_data': CallbackData.admin_chatgpt_dialog_view + str(d['id'])}
        kb.append(InlineKeyboardButton(
            d['title'] + ' ' + _('icon', d['language_code']),
            callback_data=CallbackData.admin_chatgpt_dialog_view + str(d['id'])
        ))

    kb = BotKeyboard.create_inline_keyboard(kb, row_width=2)
    kb.add(InlineKeyboardButton(
        _('inline_create_dialog'),
        callback_data=CallbackData.admin_chatgpt_create_dialog
    ))
    kb.add(InlineKeyboardButton(
        _('inline_back_to'),
        callback_data=CallbackData.admin_chatgpt
    ))

    return msg, kb

async def parse_chatgpt_dialog_view(dialog_id):
    """ Настройки системного диалога ChatGPT
    """
    dialog = await db.get_dialog({'id': dialog_id})
    dialig_id = dialog[0]['id']

    animation_mode = _('dict_animation_mode')

    pm = CallbackData.admin_chatgpt_dialog_set + "{0}." + dialog_id
    dialog[0]['language_code'] = _('name', dialog[0]['language_code'])
    dialog[0]['animation_text'] = animation_mode[dialog[0]['animation_text']]
    dialog[0]['role'] = escape_markdown(dialog[0]['role'])
    dialog[0]['welcome_message'] = dialog[0]['welcome_message'] or '-'

    msg = _('admin_chatgpt_dialog_view').format(**dialog[0])
    kb = InlineKeyboardMarkup()

    # против такого решения, но пока деваться некуда
    kb.row(
        # PARAMS
        InlineKeyboardButton(_('inline_parameters'), callback_data='_')
    ).row(
        InlineKeyboardButton(
            _('inline_dialog_param_title'), callback_data=pm.format('title')
        ),
        InlineKeyboardButton(
            _('inline_dialog_param_role'), callback_data=pm.format('role')
        ),
    ).row(
        InlineKeyboardButton(
            _('inline_dialog_param_model'), callback_data=pm.format('model')
        ),
        InlineKeyboardButton(
            _('inline_dialog_param_mhm'), callback_data=pm.format('count_history_messages')
        ),
    ).row(
        InlineKeyboardButton(
            _('inline_dialog_param_temperature'), callback_data=pm.format('temperature')
        ),
        InlineKeyboardButton(
            _('inline_dialog_param_top_p'), callback_data=pm.format('top_p')
        ),
    ).row(
        InlineKeyboardButton(
            _('inline_dialog_param_presence_penalty'), callback_data=pm.format('presence_penalty')
        ),
        InlineKeyboardButton(
            _('inline_dialog_param_frequency_penalty'), callback_data=pm.format('frequency_penalty')
        ),
    ).row(
        InlineKeyboardButton(_('inline_edit_welcome_message'), callback_data=pm.format('welcome_message'))
    ).row(
        InlineKeyboardButton(
            dialog[0]['animation_text'], callback_data=pm.format('animation')
        ),
    ).row(
        InlineKeyboardButton(_('inline_actions'), callback_data='_')
    ).row(
        InlineKeyboardButton(_('inline_dialog_delete'), callback_data=pm.format('delete'))
    )

    kb.add(InlineKeyboardButton(
        _('inline_back_to'),
        callback_data=CallbackData.admin_chatgpt_dialogs
    ))

    return msg, kb

@bot.callback_query_handler(is_chat=False,func=lambda call: call.data == CallbackData.admin_chatgpt_dialogs, role=['admin', 'demo'])
async def admin_chatgpt(call):
    """ Главная системных диалогов ChatGPT
    """
    msg, kb = await parse_chatgpt_dialogs()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_chatgpt_dialog_view), role=['admin', 'demo'])
async def admin_chatgpt(call):
    """ Страница редактирования диалога ChatGPT
    """
    await bot.delete_state(call.from_user.id)

    dialog_id = call.data.replace(CallbackData.admin_chatgpt_dialog_view, "")
    msg, kb = await parse_chatgpt_dialog_view(dialog_id)
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode = 'HTML'
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_chatgpt_create_dialog, role=['admin'])
async def admin_chatgpt_create_dialog(call):
    """ Создание диалога

        1. Выбор языка
    """
    kb = {
        _('name', l): {'callback_data': CallbackData.admin_chatgpt_create_dialog_lang+l}
        for l in lang_variants
    }
    kb.update({
        _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt_dialogs}
    })

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('choose_dialog_language'),
        reply_markup = BotKeyboard.smart(kb)
    )
    await bot.set_state(call.from_user.id, AdminChatGpt.D1)

@bot.callback_query_handler(is_chat=False, state=AdminChatGpt.D1, func=lambda call: call.data.startswith(CallbackData.admin_chatgpt_create_dialog_lang), role=['admin'])
async def admin_chatgpt_create_dialog(call):
    """ Создание диалога

        2. Сохранение выбранного языка
           и ввод названия диалога
    """
    select_language = call.data.replace(CallbackData.admin_chatgpt_create_dialog_lang, '')

    async with bot.retrieve_data(call.from_user.id) as data:
        data['lang'] = select_language

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('choose_dialog_title'),
        reply_markup = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt_dialogs}
        }),
    )
    await bot.set_state(call.from_user.id, AdminChatGpt.D2)

@bot.message_handler(is_chat=False, state=AdminChatGpt.D2, role=['admin'])
async def admin_chatgpt_create_dialog(message):
    """ Создание диалога

        3. Сохранение введённого имени
           и ввод стиля диалога
    """

    async with bot.retrieve_data(message.from_user.id) as data:
        data['title'] = message.text

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = _('choose_dialog_role'),
        reply_markup = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt_dialogs}
        }),
    )
    await bot.set_state(message.from_user.id, AdminChatGpt.D3)

@bot.message_handler(is_chat=False, state=AdminChatGpt.D3, role=['admin'])
async def admin_chatgpt_create_dialog(message):
    """ Создание диалога

        4. Сохранение введённого стиля
           и сохранение в базе
    """
    user = u.get()

    async with bot.retrieve_data(message.from_user.id) as data:
        try:
            data['role'] = message.text
            dialog_id = await db.create_dialog(
                user_id=user['id'],
                title=data['title'],
                role=escape_markdown(data['role']),
                is_system = 1,
                model = config.get('openai', 'model')
            )

            await bot.send_message(
                chat_id      =  message.from_user.id,
                text         = _('dialog_created'),
                reply_markup = BotKeyboard.smart({
                    _('inline_get_edit'): {'callback_data': CallbackData.admin_chatgpt_dialog_view+str(dialog_id)},
                    _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt_dialogs}
                }),
            )
        except Exception as e:
            print(e)
    await bot.delete_state(message.from_user.id)


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_chatgpt_dialog_delete), role=['admin'])
async def delete_chatgpt_settings(call):
    """ Удаляет диалог
    """
    dialog_id = call.data.replace(CallbackData.admin_chatgpt_dialog_delete, '')

    await db.update_dialog(dialog_id=dialog_id, args={'is_active': 0})

    kb = BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt_dialogs},
    })
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('chatgpt_dialog_success_deactivate'),
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_chatgpt_dialog_set), role=['admin'])
async def update_chatgpt_dialog(call):
    """ Обновляет настройки диалога ChatGPT
    """
    raw_param = call.data.replace(CallbackData.admin_chatgpt_dialog_set, '').split('.')

    param = raw_param[0]
    dialog_id = raw_param[1]

    dialog = await db.get_dialog({'id': dialog_id})
    msg, kb = _('service_disabled'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt_dialog_view+dialog_id}
    })

    if not param:
        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )

    if param == 'animation':
        animation = 1 if dialog[0]['animation_text'] == 0 else 0
        await db.update_dialog(
            dialog_id=dialog_id,
            args={'animation_text': animation}
        )
        msg, kb = await parse_chatgpt_dialog_view(dialog_id)
        await bot.edit_message_text(
            chat_id      = call.from_user.id,
            message_id   = call.message.message_id,
            text         = msg,
            reply_markup = kb,
            parse_mode = 'HTML'
        )
        return

    if param == 'delete':
        await bot.edit_message_text(
            chat_id      = call.from_user.id,
            message_id   = call.message.message_id,
            text         = _('delete_dialog').format(dialog[0]['title']),
            reply_markup = BotKeyboard.smart({
                _('inline_delete_dialog'): {'callback_data': CallbackData.admin_chatgpt_dialog_delete+dialog_id},
                _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt_dialog_view+dialog_id}
            })
        )
        return None

    dict_param = _('dict_dialogs_params').get(param)
    msg = _('input_new_value_param').format(dict_param)

    if param == 'model':
        msg += '\n\n' + "\n".join(list(openai_chatgpt_models().keys()))

    await bot.set_state(call.from_user.id, AdminChatGpt.C1)

    async with bot.retrieve_data(call.from_user.id) as data:
        data['param'] = param
        data['dialog_id'] = dialog_id

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.message_handler(is_chat=False, state=AdminChatGpt.C1, role=['admin', 'demo'])
async def update_chatgpt_dialog(message):
    """ Сохранение настроек диалога ChatGPT
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text

        dialog_id = data['dialog_id']
        param = data['param']

        dict_param = _('dict_dialogs_params')[param]

        msg = _('param_value_updated').format(dict_param)
        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt_dialog_view+dialog_id}
        })

        if param in ['top_p', 'temperature', 'frequency_penalty', 'presence_penalty', 'count_history_messages']:
            try:
                new_val = float(new_val)
            except Exception as e:
                new_val = 0

        models = "\n".join(list(openai_chatgpt_models().keys()))
        if param == 'model' and new_val not in models:
            msg += _('input_not_reccomend_variants')

        await db.update_dialog(dialog_id=dialog_id, args={param: new_val})

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )

    await bot.delete_state(message.from_user.id)
