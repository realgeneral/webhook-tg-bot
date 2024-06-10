from loader import bot, config, db, _, u
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

async def shop_home():
    """ Главная настроек магазина
    """
    return _('admin_shop'), BotKeyboard.smart({
        _('inline_admin_shop_tariffs'): {'callback_data': CallbackData.admin_shop_tariffs},
        _('inline_admin_shop_providers'): {'callback_data': CallbackData.admin_shop_providers},
        _('inline_admin_pay_txs'): {'callback_data': CallbackData.admin_pay_txs},
        _('inline_back_to'): {'callback_data': CallbackData.admin_home},
    })

@bot.callback_query_handler(func=lambda call: call.data == CallbackData.admin_shop, is_chat=False, role=['admin', 'demo'])
async def callback_handler(call):
    """ Меню настроек
    """
    msg, kb = await shop_home()
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=msg,
        parse_mode="Markdown",
        reply_markup=kb
    )
