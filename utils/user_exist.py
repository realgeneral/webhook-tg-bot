# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config, _, u
from .subscriptions import check_subscription
from telebot.types import Message, CallbackQuery
from keyboards.inline import BotKeyboard
from telebot.formatting import escape_markdown
from states.states import BotState
import asyncio

async def is_user(user, message: Message):
    """ Создаёт пользователя и проверяет какой язык был выбран,
        была ли произведена подписка на канал (перед использованием)
    """
    telegram_user_id = message.from_user.id

    # Если пользователя не существует, создаём
    if user is None:
        reffer_user = None
        reffer_id = 0
        reffer_id_msg = message.text.replace("/start ", "")

        if (
            config.getboolean('default', 'affiliate') and
            reffer_id_msg.startswith("ref")
        ):
            reffer_id = reffer_id_msg.replace("ref", "")
            reffer_user = await db.get_user(reffer_id)

            if reffer_user:
                reffer_id = int(reffer_user['id'])


        new_user = await db.create_user(
            telegram_id   = message.from_user.id,
            username      = message.from_user.username or _('neurouser'),
            reffer_id     = reffer_id,
            balance       = config.getint('default', 'free_tokens')
        )

        if reffer_user:
            # Повторяется из-за перехвата from_user_id
            # Создаю платёж в базе для начисления средств рефералу
            await db.create_payment({
                'from_user_id':        new_user,
                'user_id':             reffer_user['id'],
                'proxy_amount':        config.getint('default', 'affiliate_tokens'),
                'label':               f'{new_user} -> {reffer_user["id"]}',
                'type':                'refferal',
                'status':              'success',
            })

        user = {'language_code': "nill"}

        # сообщение о welcome gift отпрвляем если он больше 0
        if config.getint('default', 'free_tokens') > 0:
            msg = _('welcome_gift', message.from_user.language_code).format(**{
                "first_name": escape_markdown(message.from_user.first_name),
                "free_tokens": config.getint('default', 'free_tokens')
            })
            await bot.send_message(
                chat_id    = message.chat.id,
                text       = msg,
                parse_mode = "Markdown"
            )

    # Проверяем, выбран ли язык интерфейса
    if user['language_code'] == 'nill':
        await bot.send_message(
            chat_id      = message.chat.id,
            text         = _('choose_language', 'reben'),
            parse_mode   = "Markdown",
            reply_markup = BotKeyboard.choose_language()
        )
        return False

    return True
