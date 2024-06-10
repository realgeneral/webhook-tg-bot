# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from utils.logging import logging
from loader import db, config, bot, _
from telebot.util import antiflood

from keyboards.inline import BotKeyboard
from utils.strings import CallbackData

import asyncio

directive = 'bonuses'

async def bonus_accrual() -> None:
    """ Добавляет ежедневный бонус пользователям, если включена опция
    """
    if not config.getboolean(directive, 'status'):
        return

    users = await db.get_raw(f"""
        SELECT *
        FROM users
        WHERE
            type = 'user' AND
            role IN ('user', 'admin') AND
            is_active =  1 AND
            balance <= {config.get(directive, 'min_balance')} AND
            DATE(created_at) != CURDATE()
            AND id NOT IN (
                SELECT user_id
                FROM payments
                WHERE `type` = 'bonus'
                AND DATE(created_at) = CURDATE()
            )
    """)

    system_dialog = await db.get_dialog(
        {'is_system': 1, 'language_code': 'ru'},
        end_limit = 1
    )

    for user in users:
        lang = user['language_code']

        try:
            # Уведомляем пользователя о начислении
            if config.getboolean(directive, 'notification'):
                await bot.send_message(
                    chat_id = user['telegram_id'],
                    text = _('bonus_accrual', lang).format(**{
                        'tokens': config.getint(directive, 'bonus')
                    }),
                    reply_markup = BotKeyboard.smart({
                        _('inline_start_chat_gpt'): {
                            'callback_data': CallbackData.start_chatgpt_dialog + str(system_dialog[0]['id'])
                        },
                        _('inline_dalle'): {
                            'callback_data': CallbackData.dalle
                        },
                        _('inline_stable_diffusion'): {
                            'callback_data': CallbackData.stable_diffusion
                        },
                        _('inline_buy_tokens'): {
                            'callback_data': CallbackData.home_shop
                        },
                    })
                )
            # Создаём платеж
            await db.create_payment({
                'user_id':             user['id'],
                'proxy_amount':        config.get(directive, 'bonus'),
                'type':                'bonus',
                'close':               0,
                'status':              'success',
            })
            # Засыпаем (чтобы телега не банила)
            await asyncio.sleep(1.25)
        except Exception as e:
            # Помечаем пользователя как неактивного
            await db.set_raw(
                f"UPDATE users SET is_active = 0 WHERE id = {user['id']}"
            )
            logging.warning(f"Пользователь {user['telegram_id']} удалил бот, ошибка: {str(e)}")

async def bonus_burn() -> None:
    """ Сжигает бонусы в конце дня
    """
    if not config.getboolean(directive, 'status'):
        return

    try:
        users = await db.get_raw(f"""
            SELECT
                u.id,
                u.balance,
                u.telegram_id,
                COALESCE((
                    SELECT SUM(total_tokens)
                    FROM requests r
                    WHERE r.user_id = u.id AND DATE(r.created_at) = CURDATE()
                ), 0) as total_tokens
            FROM users u
            WHERE
                u.id IN (
                    SELECT p.user_id
                    FROM payments p
                    WHERE p.type = 'bonus'
                    AND DATE(p.created_at) = CURDATE()
                ) AND
                u.id NOT IN (
                    SELECT p.user_id
                    FROM payments p
                    WHERE p.type = 'burn_bonus'
                    AND DATE(p.created_at) = CURDATE()
                )
            HAVING
                total_tokens <= {config.get(directive, 'bonus')}
        """)

        for user in users:
            burn = config.getint(directive, 'bonus') - user['total_tokens']

            # Создаём платеж
            await db.create_payment({
                'user_id':             user['id'],
                'proxy_amount':        burn,
                'type':                'burn_bonus',
                'close':               0,
                'status':              'success',
            })

            await db.set_raw(f"""
                UPDATE users
                SET balance = balance - {burn}
                WHERE id = {user['id']}
            """)
    except Exception as e:
        logging.warning(e)
