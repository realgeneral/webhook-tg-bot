# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from telebot.handler_backends import BaseMiddleware
from telebot.util import quick_markup
from telebot.types import CallbackQuery, Message
from telebot.handler_backends import CancelUpdate, SkipHandler
from languages.language import locales, lang_variants
from utils.strings import CacheData
from telebot.formatting import escape_markdown
from datetime import datetime

import contextvars

class UserBaseMiddleware(BaseMiddleware):
    """ Обработка пользователя
    """
    user     = contextvars.ContextVar('user', default=None)
    language = contextvars.ContextVar('language', default=None)

    def __init__(self, bot, db, config, cache) -> None:
        self.bot          = bot
        self.db           = db
        self.config       = config
        self.cache        = cache
        self.update_types = ['message', 'callback_query', 'inline_query']

    async def pre_process(self, message, data):
        """ pre_process
        """
        if (
            type(message) == CallbackQuery and
            message.message.chat.type in ['group', 'supergroup']
        ):
            return CancelUpdate()

        if (
            type(message) == Message and
            message.chat.type in ['group', 'supergroup']
        ):
            return CancelUpdate()

        now  = datetime.now()
        user = await self.db.get_user(message.from_user.id)

        telegram_user_id = message.from_user.id
        username = message.from_user.username

        # Если пользователя не существует, создаём
        if not user:
            reffer_user = None
            reffer_id = 0
            reffer_id_msg = message.text.replace("/start ", "")

            if (
                self.config.getboolean('default', 'affiliate') and
                reffer_id_msg.startswith("ref")
            ):
                reffer_id = reffer_id_msg.replace("ref", "")
                reffer_user = await self.db.get_user(reffer_id)

                if reffer_user:
                    reffer_id = int(reffer_user['id'])

            lcode = message.from_user.language_code  if message.from_user.language_code in lang_variants else self.config.get('default', 'language')

            new_user = await self.db.create_user(
                telegram_id   = message.from_user.id,
                username      = message.from_user.username or self.translate('neurouser'),
                reffer_id     = reffer_id,
                balance       = self.config.getint('default', 'free_tokens'),
                lang          = lcode
            )

            # DUPLICATE !!!!!!!!
            # DUPLICATE !!!!!!!!
            # DUPLICATE !!!!!!!!
            user = {
                'id': new_user,
                'telegram_id': message.from_user.id,
                'username': message.from_user.username or self.translate('neurouser', lcode),
                'language_code': lcode,
                'role': 'user',
                'is_active': 1,
                'balance': self.config.getint('default', 'free_tokens'),
                'is_subscriber': 0,
            }
            data['user'] = user
            data['language_code'] = lcode

            # Сохраняем в contextvars
            self.language.set(lcode)
            self.user.set(user)
            # DUPLICATE !!!!!!!!
            # DUPLICATE !!!!!!!!
            # DUPLICATE !!!!!!!!

            if reffer_user:
                # Повторяется из-за перехвата from_user_id
                # Создаю платёж в базе для начисления средств рефералу
                await self.db.create_payment({
                    'from_user_id':        new_user,
                    'user_id':             reffer_user['id'],
                    'proxy_amount':        self.config.getint('default', 'affiliate_tokens'),
                    'label':               f'{new_user} -> {reffer_user["id"]}',
                    'type':                'refferal',
                    'status':              'success',
                })

            # сообщение о welcome gift отпрвляем если он больше 0
            if self.config.getint('default', 'free_tokens') > 0:
                msg = self.translate('welcome_gift', lcode).format(**{
                    "first_name": escape_markdown(message.from_user.first_name),
                    "free_tokens": self.config.getint('default', 'free_tokens')
                })
                await self.bot.send_message(
                    chat_id    = message.chat.id,
                    text       = msg,
                    parse_mode = "Markdown"
                )


        if user:
            # Добавляем в кэш строку о последнем использовании ботом пользователем
            await self.cache.set(
                CacheData.last_use_bot.format(message.from_user.id),
                now.strftime(self.config.get('default', 'datetime_mask'))
            )

            # Помечаем юзера как активного (если он вдруг перезашел в бот)
            if user.get('is_active') == 0:
                await self.db.update_user(
                    telegram_user_id,
                    {'is_active': 1}
                )

            # Обновляем юзернейм, если он был изменён
            if username and user.get('username') != username:
                await self.db.update_user(telegram_user_id, {'username': username})

            # Если пользовтель заблокирован, уведомляем его об этом
            if user.get('role', 'user') == 'blocked':
                str_contact = self.translate(
                    'inline_contact_with_admin',
                    user['language_code']
                )

                await self.bot.send_message(
                    message.from_user.id,
                    self.translate('user_blocked', user['language_code']),
                )

                return

            # Задаём глобальные переменные для обращения из handlers
            data['user'] = user
            data['language_code'] = user['language_code']

            # Сохраняем в contextvars
            self.language.set(data['language_code'])
            self.user.set(user)

            return None

        data['user'] = None
        data['language_code'] = self.config['default']['language']

        self.language.set(data['language_code'])

    async def post_process(self, message, data, exception):
        """ post process
        """
        ...

    def translate(self, key: str, code: str = None) -> str:
        """ Возвращает языковую строку

            :key:  str ключ к строке
        """
        lang_code = self.language.get()

        # На случай если надо переназначить
        if code is not None:
            lang_code = code

        return locales.get(
            lang_code,
            locales.get(self.config['default']['language'])
        ).get(
            key,
            'StringNotFound'
        )
