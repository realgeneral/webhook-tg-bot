# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from telebot.asyncio_filters import SimpleCustomFilter, AdvancedCustomFilter
from telebot.types import CallbackQuery, Message
from loader import bot, db, cache, _, config, u
from telebot.asyncio_handler_backends import CancelUpdate, SkipHandler, ContinueHandling
from utils.subscriptions import check_subscription
from utils.strings import CallbackData, CacheData
from keyboards.inline import BotKeyboard
from telebot.util import extract_arguments
import logging

import datetime
import json

def remaining_seconds():
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    remaining_time = midnight - now
    remaining_seconds = remaining_time.total_seconds()
    return int(remaining_seconds)

class Role(AdvancedCustomFilter):
    """ Проверяет есть ли у пользователя
        необходимые права доступа в разделы

        (на текущий момент просто категоризирован,
         требуется переделать на конкретную выдачу прaв)
    """
    key='role'
    @staticmethod
    async def check(message: Message, roles):
        user = u.get()
        if user['role'] not in roles:
            if type(message) == CallbackQuery:
                await bot.answer_callback_query(
                    message.id,
                    _('access_denied'),
                    show_alert=True
                )

            if type(message) == Message:
                await bot.send_message(
                    message.from_user.id,
                    _('access_denied')
                )

        return user['role'] in roles

class IsChat(SimpleCustomFilter):
    """ Проверяет находится ли бот в чате
    """
    key='is_chat'
    @staticmethod
    async def check(message: Message):
        if type(message) == CallbackQuery:
            message = message.message
        return message.chat.type in ['group', 'supergroup']

class IsAction(SimpleCustomFilter):
    """ Не пропускает функцию в следующий обработчик
    """
    key='is_action'
    @staticmethod
    async def check(message: Message):
        action = await cache.get(CacheData.stop_next_handler.format(
            message.from_user.id
        ))
        if action:
            await cache.delete(CacheData.stop_next_handler.format(
                message.from_user.id
            ))
            return False
        return True

class IsSubscription(SimpleCustomFilter):
    """ Проверяет подписался ли человек на каналы
    """
    key='is_subscription'
    @staticmethod
    async def check(message: Message):
        user = u.get()

        if user.get('is_subscriber') == 1:
            return True

        try:
            msg = {
                'from_user_id': message.from_user.id,
            }

            if type(message) == Message:
                msg['chat_id'] = message.chat.id
            if type(message) == CallbackQuery:
                msg['message_id'] = message.message.message_id

            if (
                user and
                user['role'] in ['user', 'demo'] and
                config.getboolean('subscribe', 'required_subscribe') and
                await check_subscription(user, msg, False) == False
            ):
                msg = _('promotion_text')

                if config.getboolean('subscribe', 'only_one_channel'):
                    msg += _('promotion_text_only_one_channel')

                kb = await BotKeyboard.subscribe_channel(user['language_code'])

                if type(message) == Message:
                    await bot.send_message(
                        chat_id      = message.from_user.id,
                        text         = msg,
                        reply_markup = kb
                    )

                if type(message) == CallbackQuery:
                    await bot.edit_message_text(
                        chat_id      = message.from_user.id,
                        message_id   = message.message.message_id,
                        text         = msg,
                        reply_markup = kb
                    )

                await cache.set(CacheData.stop_next_handler.format(
                    message.from_user.id
                ), 0)

                return False
        except Exception as e:
            logging.warning(e)
            print(e)

        return True

class Service(AdvancedCustomFilter):
    """ Проверяем работает ли сервис

        Возвращает bool
    """
    key='service'
    @staticmethod
    async def check(message: Message, service):
        if config.getboolean('service', service) is False:
            await bot.delete_state(message.from_user.id)

            if type(message) == CallbackQuery:
                await bot.answer_callback_query(message.id, _('service_disabled'), show_alert=True)

            if type(message) == Message:
                # Удаляем стейт, на случай если это было в активном состоянии
                await bot.delete_state(message.from_user.id)
                # Уведомляем
                await bot.send_message(
                    message.from_user.id,
                    _('service_disabled'),
                    reply_markup=BotKeyboard.smart({
                        _('inline_back_to_main_menu'): {
                            'callback_data': CallbackData.user_home
                        }
                    })
                )

            return False

        return True

class Statistics(AdvancedCustomFilter):
    """ Добавляем данные об использовании сервиса в статистику

        Возвращает bool
    """
    key='stats'
    @staticmethod
    async def check(message, name):
        rkey = f'stats_{name}_{message.from_user.id}'

        try:
            user = u.get()

            point = getattr(message, 'text', 'point')
            source_stat = extract_arguments(point)
            rsource = f'stats_source_{source_stat}_{message.from_user.id}'

            if type(message) == Message and source_stat.startswith('source_') and not await cache.get(rsource):
                await db.set_raw(f"""INSERT INTO statistics (user_id, section, created_at) VALUES ("{user['id']}", "{source_stat}", "{datetime.datetime.now()}")""")
                await cache.set(rsource, 1)
                await cache.expire(rsource, remaining_seconds())

            if not await cache.get(rkey):
                await db.set_raw(f"""INSERT INTO statistics (user_id, section, created_at) VALUES ("{user['id']}", "{name}", "{datetime.datetime.now()}")""")
                await cache.set(rkey, 1)
                await cache.expire(rkey, remaining_seconds())
        except Exception as e:
            print(e)

        return True

class ControlGptDialog(AdvancedCustomFilter):
    """ Проверяет была ли вызвана в тексте языковая строка/команда
        для пропуска к обработчику

        Принимает список из двух элементов:
        [языковая строка, команда]

        Возвращает bool
    """
    key = 'control_gpt'

    @staticmethod
    async def check(message: Message, strings):
        if (
            _(strings[0]) == message.text or
            strings[1] == message.text
        ):
            return True

        return False

class ContinueCommand(AdvancedCustomFilter):
    """ Если была введена команда в разделе,
        где нам нужно перейти туда - переходим (сори за тавтологию)

        Короче если мы в условном стейбле пишем /gpt, то он не должен
        принимать как запрос, а должен перейти в гпт
    """
    key = 'continue_command'

    @staticmethod
    async def check(message: Message, type):
        if message.text in _('commands').keys():
            if type == 'delete_reply_keyboard':
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text=_('keyboard_deleted'),
                    reply_markup=BotKeyboard.remove_reply()
                )

            if type == 'gpt':
                async with bot.retrieve_data(message.from_user.id) as data:
                        dialog = json.loads(data['dialog'])
                        await bot.send_message(
                            chat_id = message.from_user.id,
                            text    = _('dialog_is_end').format(
                                dialog['title']
                            ),
                            reply_markup = BotKeyboard.remove_reply()
                        )

            await bot.delete_state(message.from_user.id)

            return False

        return True
