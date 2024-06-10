# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, _, config
from datetime import datetime, timedelta
from keyboards.inline import BotKeyboard
from utils.texts import Pluralize
from .strings import CallbackData

async def notify_admins(message: str = '', keyboard: dict = None):
    """ Отправляет уведомление администраторам
    """
    pass

async def exceed_limit(
    chat_id: int,
    lang: str,
    tokens: int = 0,
    key_string: str = 'exceeded_limit',
    type: str = 'user',
    model: str = 'empty'
) -> None:
  """ Отправляет сообщение об ограничении

     :chat_id:
     :lang:
     :tokens:
     :approximately:
  """
  string_back_to = _('inline_back_to_main_menu')
  string_shop = _('inline_shop')
  numerals_tokens = _('numerals_tokens')
  numerals_word = Pluralize.declinate(tokens, numerals_tokens, type = 2)

  msg = _(key_string).format(**{
    'amount_tokens': numerals_word.number,
    'p1': numerals_word.word,
    'ref_tokens': config.getint('default', 'affiliate_tokens')
  })
  kb = {
    string_shop: {'callback_data': CallbackData.home_shop},
    _('inline_refferal_program'): {'callback_data': CallbackData.refferal_program}
  }

  if (
    config.getboolean('subscribe', 'unlim_gpt35turbo') and
    model.startswith('gpt-3.5')
  ):
      msg += _('exceeded_limit_gpt35')
      kb.update({
        _('inline_unlim_gpt'): {'callback_data': CallbackData.unlim_gpt35turbo}
      })

  kb.update({
    string_back_to: {'callback_data': CallbackData.user_home}
  })

  await bot.send_message(
      chat_id      = chat_id,
      text         = msg,
      reply_markup = BotKeyboard.smart(kb) if type == 'user' else None
  )
