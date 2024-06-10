# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u, loop
from languages.language import lang_variants
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from states.states import AdminStable
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.configurable import config_update

async def parse_stable():
    """ Главное меню Stable Diffusion
    """
    service_status = _('dict_service_status')[config.getboolean('service', 'stable_diffusion')]

    msg = _('admin_stable_diffusion').format(**{
        "mode":  service_status,
        "engine": config.get('stable_diffusion', 'engine'),
        "tti_price": config.get('stable_diffusion', 'tti_price'),
        "iti_price": config.get('stable_diffusion', 'iti_price')
    })

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(_('inline_parameters'), callback_data='_')
    ).row(
        InlineKeyboardButton(
            service_status, callback_data=CallbackData.admin_stable_set_param+'mode'
        ),
    ).row(
        InlineKeyboardButton(_('inline_stable_engine'), callback_data=CallbackData.admin_stable_set_param+'engine')
    ).row(
        InlineKeyboardButton(_('inline_stable_tti_price'), callback_data=CallbackData.admin_stable_set_param+'tti_price')
    ).row(
        InlineKeyboardButton(_('inline_stable_iti_price'), callback_data=CallbackData.admin_stable_set_param+'iti_price')
    ).row(
        InlineKeyboardButton(
            _('inline_back_to'), callback_data=CallbackData.admin_home
        )
    )

    return msg, kb

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_stable, role=['admin', 'demo'])
async def admin_stable(call):
    """ Главная настроек Dall-E
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_stable()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_stable_set_param), role=['admin'])
async def update_chatgpt_settings(call):
    param = call.data.replace(CallbackData.admin_stable_set_param, '')
    msg, kb = _('service_disabled'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_stable}
    })

    if not param:
        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )

    if param == 'mode':
        mode = config.get('service', 'stable_diffusion')
        new_value = 'False' if mode == 'True' else 'True'
        config.set('service', 'stable_diffusion', new_value)
        await config_update()
        msg, kb = await parse_stable()

    if param in ['tti_price', 'iti_price', 'engine']:
        dict_param = _('dict_config_params')[param]
        msg = _('input_new_value_param').format(dict_param)

        await bot.set_state(call.from_user.id, AdminStable.A1)

        async with bot.retrieve_data(call.from_user.id) as data:
            data['param'] = param

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.message_handler(is_chat=False, state=AdminStable.A1, role=['admin'])
async def stable_save(message):
    """ Сохранение настроек SD
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text

        param = data['param']
        dict_param = _('dict_config_params')[param]

        msg = _('param_value_updated').format(dict_param)
        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_stable}
        })

        if param in ['tti_price', 'iti_price']:
            try:
                new_val = int(new_val)
            except Exception as e:
                new_val = 0

        config.set('stable_diffusion', param, str(new_val))

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )

    await bot.delete_state(message.from_user.id)
    await config_update()
