# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u, loop
from languages.language import lang_variants
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from states.states import AdminChatGpt
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.configurable import config_update
from utils.functions import openai_chatgpt_models

async def parse_chatgpt():
    """ Главное меню ChatGPT
    """
    service_status = _('dict_service_status')[config.getboolean('service', 'gpt')]
    speech_status = _('dict_speech_status')[config.getboolean('openai', 'speech')]

    msg = _('admin_openai_chatgpt').format(**{
        "mode":               service_status,
        "model":              config.get('openai', 'model'),
        "mhs":                config.get('openai', 'max_history_message'),
        "md":                 config.get('openai', 'max_custom_gpt_dialogs'),
        "added_value_gpt":    config.get('openai', 'added_value_gpt'),
        "added_value_speech": config.get('openai', 'added_value_speech'),
        "speech_status":      speech_status,
    })

    kb = InlineKeyboardMarkup()

    kb.row(
        InlineKeyboardButton(_('inline_parameters'), callback_data='_')
    ).row(
        InlineKeyboardButton(service_status, callback_data=CallbackData.admin_chatgpt_set_param+'mode'),
        InlineKeyboardButton(_('inline_chatgpt_param_model'), callback_data=CallbackData.admin_chatgpt_set_param+'model'),
    ).row(
        InlineKeyboardButton(_('inline_chatgpt_param_cd'), callback_data=CallbackData.admin_chatgpt_set_param+'max_custom_gpt_dialogs'),
        InlineKeyboardButton(_('inline_chatgpt_param_mhs'), callback_data=CallbackData.admin_chatgpt_set_param+'max_history_message')
    ).row(
        InlineKeyboardButton(_('inline_added_value_gpt'), callback_data=CallbackData.admin_chatgpt_set_param+'added_value_gpt'),
        InlineKeyboardButton(_('inline_admin_chatgpt_reset_model'), callback_data=CallbackData.admin_chatgpt_set_param+'reset')
    ).row(
        InlineKeyboardButton(_('inline_dalle_param_speech_price'), callback_data=CallbackData.admin_chatgpt_set_param+'added_value_speech')
    ).row(
        InlineKeyboardButton(speech_status, callback_data=CallbackData.admin_chatgpt_set_param+'mode_speech')
    ).row(
        InlineKeyboardButton(_('inline_section'), callback_data='_')
    ).row(
        InlineKeyboardButton(_('inline_admin_chatgpt_dialogs'), callback_data=CallbackData.admin_chatgpt_dialogs)
    ).row(
        InlineKeyboardButton(_('inline_back_to'), callback_data=CallbackData.admin_openai)
    )

    return msg, kb

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_chatgpt, role=['admin', 'demo'])
async def admin_chatgpt(call):
    """ Главная настроек ChatGPT
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_chatgpt()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_chatgpt_set_param), role=['admin'])
async def update_chatgpt_settings(call):
    """ Обновляет настройки ChatGPT
    """
    param = call.data.replace(CallbackData.admin_chatgpt_set_param, '')
    msg, kb = _('service_disabled'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt}
    })

    if not param:
        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )

    if param == 'reset':
        model = config.get('openai', 'model')
        msg = _('reset_model_in_dialogs_success').format(**{'model': model})

        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )
        await db.many_dialogs_update({'model': model})

        return None

    if param == 'mode_speech':
        mode = config.get('openai', 'speech')
        new_value = 'False' if mode == 'True' else 'True'
        config.set('openai', 'speech', new_value)
        await config_update()
        msg, kb = await parse_chatgpt()

    if param == 'mode':
        mode = config.get('service', 'gpt')
        new_value = 'False' if mode == 'True' else 'True'
        config.set('service', 'gpt', new_value)
        await config_update()
        msg, kb = await parse_chatgpt()

    if param in ['model', 'max_custom_gpt_dialogs', 'max_history_message', 'added_value_gpt', 'added_value_speech']:
        dict_param = _('dict_config_params')[param]
        msg = _('input_new_value_param').format(dict_param)

        if param == 'model':
            msg += '\n\n' + "\n".join(list(openai_chatgpt_models().keys()))

        await bot.set_state(call.from_user.id, AdminChatGpt.B1)

        async with bot.retrieve_data(call.from_user.id) as data:
            data['param'] = param

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.message_handler(is_chat=False, state=AdminChatGpt.B1, role=['admin'])
async def admin_chatgpt_create_dialog(message):
    """ Сохранение настроек ChatGPT
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text

        param = data['param']
        dict_param = _('dict_config_params')[param]

        msg = _('param_value_updated').format(dict_param)
        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_chatgpt}
        })

        models = openai_chatgpt_models()
        if param == 'model' and new_val not in list(models.keys()):
            msg += _('input_not_reccomend_variants')

        if param in ['max_custom_gpt_dialogs', 'max_history_message', 'added_value_gpt', 'added_value_speech']:
            try:
                new_val = int(new_val)
            except Exception as e:
                new_val = 0

        config.set('openai', param, str(new_val))

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )

    await bot.delete_state(message.from_user.id)
    await config_update()
