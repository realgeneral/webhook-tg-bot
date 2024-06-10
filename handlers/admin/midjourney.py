# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, config, db, _, u, loop
from languages.language import lang_variants
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from states.states import AdminMJ
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.configurable import config_update

async def parse_midjourney():
    """ Главное меню Midjourney
    """
    service_status = _('dict_service_status')[config.getboolean('service', 'midjourney')]

    msg = _('admin_midjourney').format(**{
        "mode":  service_status,
        "mj_mode": config.get('midjourney', 'mode'),
        "tti_price": config.get('midjourney', 'tti_price'),
        "base_upscale_price": config.get('midjourney', 'base_upscale_price'),
        "info_link": config.get('midjourney', 'info_link'),
    })

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(_('inline_parameters'), callback_data='_')
    ).row(
        InlineKeyboardButton(
            service_status, callback_data=CallbackData.admin_mj_set_param+'mode'
        ),
    ).row(
        InlineKeyboardButton(_('inline_mj_mode'), callback_data=CallbackData.admin_mj_set_param+'mj_mode')
    ).row(
        InlineKeyboardButton(_('inline_stable_tti_price'), callback_data=CallbackData.admin_mj_set_param+'mj_tti_price')
    ).row(
        InlineKeyboardButton(_('inline_stable_upscale_price'), callback_data=CallbackData.admin_mj_set_param+'base_upscale_price')
    ).row(
        InlineKeyboardButton(_('inline_change_info_link'), callback_data=CallbackData.admin_mj_set_param+'info_link')
    ).row(
        InlineKeyboardButton(
            _('inline_back_to'), callback_data=CallbackData.admin_home
        )
    )

    return msg, kb

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_midjourney, role=['admin', 'demo'])
async def admin_mj(call):
    """ Главная настроек MJ
    """
    await bot.delete_state(call.from_user.id)

    msg, kb = await parse_midjourney()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = 'HTML',
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_mj_set_param), role=['admin'])
async def adm_update_mj_settings(call):
    param = call.data.replace(CallbackData.admin_mj_set_param, '')
    msg, kb = _('service_disabled'), BotKeyboard.smart({
        _('inline_back_to'): {'callback_data': CallbackData.admin_midjourney}
    })

    if not param:
        await bot.answer_callback_query(
            call.id,
            text       = msg,
            show_alert = True
        )

    if param == 'mode':
        mode = config.get('service', 'midjourney')
        new_value = 'False' if mode == 'True' else 'True'
        config.set('service', 'midjourney', new_value)
        await config_update()
        msg, kb = await parse_midjourney()

    if param in ['mj_tti_price', 'base_upscale_price', 'mj_mode', 'info_link']:
        dict_param = _('dict_config_params')[param]
        msg = _('input_new_value_param').format(dict_param)

        await bot.set_state(call.from_user.id, AdminMJ.A1)

        async with bot.retrieve_data(call.from_user.id) as data:
            data['param'] = param

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = 'HTML',
    )

@bot.message_handler(is_chat=False, state=AdminMJ.A1, role=['admin'])
async def adm_mj_save(message):
    """ Сохранение настроек Mj
    """
    async with bot.retrieve_data(message.from_user.id) as data:
        new_val = message.text

        param = data['param']
        dict_param = _('dict_config_params')[param]

        msg = _('param_value_updated').format(dict_param)
        kb = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.admin_midjourney}
        })

        if param in ['mj_mode']:
            param = 'mode'

        if param in ['mj_tti_price', 'base_upscale_price']:
            try:
                new_val = int(new_val)
                if param in ['mj_tti_price']:
                    param = 'tti_price'
            except Exception as e:
                new_val = 0

        config.set('midjourney', param, str(new_val))

        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = msg,
            reply_markup = kb,
        )

    await bot.delete_state(message.from_user.id)
    await config_update()
