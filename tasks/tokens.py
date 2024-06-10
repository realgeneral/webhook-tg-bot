# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from utils.logging import logging
from loader import db, config, bot, _, cache
from telebot.util import antiflood

from keyboards.inline import BotKeyboard
from utils.strings import CallbackData
from datetime import datetime

import asyncio

async def subscription() -> None:
    """ Проверяет / отменяет текущие подписки
        и отправляет уведомления о завершении

        - Остался день до окончания подписки: уведомляет об этом
        - Израсходованы токены: уведомляет о том, что можно продлить
        - Подписка закончена: останавливает и уведомляет
    """

    subscriptions = await db.get_raw(f"""
        SELECT *  FROM subscriptions  WHERE status = 'active'
    """)

    if not subscriptions:
        return False

    for sub in subscriptions:
        user = await db.get_user(sub['user_id'], name_id="id")
        msg, kb = None, {}

        remaining = sub['expires_at']
        rem_tokens = await db.get_raw(f"""
           SELECT
               sum(total_tokens) as tokens
           FROM requests
           WHERE
               `user_id` = {sub['user_id']} AND
               `unlimited` = 0 AND
               `is_sub` = 1 AND
               UNIX_TIMESTAMP(created_at) >= UNIX_TIMESTAMP('{sub['created_at']}')
        """)
        unspent_tokens = sub['tokens'] - (rem_tokens[0]['tokens'] or 0)

        if datetime.now() > remaining:

            await cache.delete(f'unlimsub_{sub["user_id"]}')

            msg = _('subscribe_ended')
            await db.set_raw(f"""
               UPDATE subscriptions SET status = 'inactive' WHERE id = {sub['id']}
            """)

            kb.update({
                _('inline_subscribe'): {'callback_data': CallbackData.home_shop}
            })

            await db.set_raw(f"""
                UPDATE users SET is_subscriber = 1 WHERE id = {sub['user_id']};
            """)

            if unspent_tokens > 0:
                add_tokens = 0
                # add_tokens = (unspent_tokens / 100) * config.getint('shop', 'unspent_percent')

                burn_balance = unspent_tokens - add_tokens

                await db.create_payment({
                    'user_id':             user['id'],
                    'proxy_amount':        burn_balance,
                    'type':                'burn',
                    'close':               1,
                    'status':              'success',
                })

                await db.set_raw(f"""
                   UPDATE users SET balance = balance - {burn_balance}  WHERE id = {sub['user_id']}
                """)

        one_day = remaining - datetime.now()

        # if (
        #     sub['tomorrow_notify'] == 0 and
        #     sub['autopayment'] == 1 and
        #     one_day.days == 0 and
        #     one_day.seconds <= 82800
        # ):
        #     # Пока только для юкассы, позже будет общий драйвер
        #     autopayment_data = sub['data']
        #     autopayment_data.get('name')
        #     # getattr()

        if (
            sub['tomorrow_notify'] == 0 and
            sub['autopayment'] == 0 and
            one_day.days == 0 and
            one_day.seconds <= 82800
        ):
            msg = _('tomorrow_subscribe_ended').format(**{
                'date': remaining.strftime(config.get('default', 'datetime_mask'))
            })
            await db.set_raw(f"""
               UPDATE subscriptions SET tomorrow_notify = 1 WHERE id = {sub['id']}
            """)
            kb.update({
                _('inline_update_subscribe'): {'callback_data': CallbackData.home_shop}
            })

        if sub['spent_nofity'] == 0 and unspent_tokens <= 0:
            await cache.set(f'unlimsub_{sub["user_id"]}', 1)
            msg = _('spent_subscribe_tokens')
            await db.set_raw(f"""
               UPDATE subscriptions SET spent_nofity = 1 WHERE id = {sub['id']}
            """)
            kb.update({
                _('inline_up_subscribe'): {'callback_data': CallbackData.home_shop}
            })

        if not msg:
            continue

        try:
            kb.update({
                _('inline_back_to'): {'callback_data': CallbackData.user_home}
            })
            await bot.send_message(
                chat_id      = user['telegram_id'],
                text         = msg,
                reply_markup = BotKeyboard.smart(kb)
            )
        except Exception as e:
            # Помечаем пользователя как неактивного
            await db.set_raw(
                f"UPDATE users SET is_active = 0 WHERE id = {user['id']}"
            )
            logging.warning(f"Пользователь {user['telegram_id']} удалил бот, ошибка: {str(e)}")
