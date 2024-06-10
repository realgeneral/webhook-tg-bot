from loader import db, bot, _, config, cache
from keyboards.inline import BotKeyboard
from utils.strings import CallbackData, CacheData
from utils.payment_providers import payment_drivers
from utils.texts import Pluralize
from datetime import datetime, timedelta
from handlers.user.shop import get_tariff_name
from utils.logging import logging

import json

# в этой папке будет храниться логика бота / бизнес функции

# в топку
class Balance:
    def __init__(self, db):
        self.db = db
        self.user = None

    async def activate_subscribe():
        pass

    async def deactivate_subscribe():
        pass

    async def accept_payment(self, payment_id, data = {}):
        """ Подтверждает платеж
        """
        payment = await self.db.get_payment({
            'id': payment_id,
            'type': 'tx',
            'close': 0
        })

        autopayment = 0

        if not payment:
            return False

        payment = payment[0]

        if type(data) == dict and data.get('payment_method'):
            data = data.get('payment_method')
            autopayment = 1

        await self.db.update_payment(
            payment_id,
            {
                'status': 'success',
                'close': 1
            }
        )

        self.user = await self.db.get_user(payment['user_id'], name_id="id")

        if self.user['reffer_id'] != 0:
            payment_type = 'refferal'
            percent = config.getint('default', 'affiliate_payment_percent')
            refferal_amount = (payment['proxy_amount'] / 100) * percent

            if config.getboolean('default', 'affiliate_cash_mode'):
                payment_type = 'refferal_cash'
                refferal_amount = (payment['amount'] / 100) * percent

            await self.db.create_payment({
                'from_user_id':        self.user['id'],
                'user_id':             self.user['reffer_id'],
                'amount':              refferal_amount,
                'proxy_amount':        refferal_amount,
                'label':               payment['id'],
                'type':                payment_type,
                'status':              'success',
            })

            if payment_type == 'refferal_cash':
                await db.set_raw(f"""
                    INSERT INTO wallets
                        (user_id, type, currency, balance)
                    VALUES  (
                        {self.user['reffer_id']},
                        '{payment_type}',
                        '{payment['currency']}',
                        {refferal_amount}
                    )
                    ON DUPLICATE KEY UPDATE
                        balance = balance + VALUES(balance);
                """)

        numerals_tokens = _('numerals_tokens', self.user['language_code'])
        string_proxy_amount = Pluralize.declinate(payment['proxy_amount'], numerals_tokens)

        msg_string = 'success_payment'

        tariff = await self.db.get_tariff({'id': payment['tariff_id']})
        remaining = datetime.now() + timedelta(days=tariff[0]['days_before_burn'])

        remaining_notify = remaining - datetime.now()

        if tariff[0]['days_before_burn'] > 0:
            # payment_method
            msg_string = 'success_sub_payment'
            current_sub = await self.db.get_raw(f"SELECT * FROM subscriptions WHERE user_id = {self.user['id']} AND status = 'active' ORDER BY id DESC")

            if current_sub:
                 await self.db.set_raw(f"""
                    UPDATE subscriptions SET status = 'inactive' WHERE id = {current_sub[0]['id']}
                 """)
                 rem_tokens = await db.get_raw(f"""
                    SELECT
                        sum(total_tokens) as tokens
                    FROM requests
                    WHERE
                        `user_id` = {self.user['id']} AND
                        `unlimited` = 0 AND
                        `is_sub` = 1 AND
                        UNIX_TIMESTAMP(created_at) >= UNIX_TIMESTAMP('{current_sub[0]['created_at']}')
                 """)
                 unspent_tokens = current_sub[0]['tokens'] - (rem_tokens[0]['tokens'] or 0)

                 if unspent_tokens > 0:
                     add_tokens = (unspent_tokens / 100) * config.getint('shop', 'unspent_percent')
                     payment['proxy_amount'] += add_tokens

                     burn_balance = unspent_tokens - add_tokens

                     await db.create_payment({
                         'user_id':             self.user['id'],
                         'proxy_amount':        burn_balance,
                         'type':                'burn',
                         'close':               1,
                         'status':              'success',
                     })

                     await db.set_raw(f"""
                        UPDATE users SET balance = balance - {burn_balance}  WHERE id = {self.user['id']}
                     """)

            await db.create_subscribe({
                'user_id':     self.user['id'],
                'amount':      tariff[0]['amount'],
                'provider_id': payment['payment_provider_id'],
                'tokens':      payment['proxy_amount'],
                'autopayment': autopayment,
                'data':        data,
                'expires_at':  remaining,
            })

            await db.set_raw(f"""
                UPDATE users SET is_subscriber = 1 WHERE id = {self.user['id']};
            """)


        msg = _(msg_string, self.user['language_code']).format(**{
            "name":       get_tariff_name(tariff[0]),
            "date":       remaining.strftime(config.get('default', 'datetime_mask')),
            "tokens":     payment['proxy_amount'],
            "p1":         string_proxy_amount.word,
            "payment_id": payment['id']
        })
        kb = BotKeyboard.smart({
            _('inline_profile', self.user['language_code']): {"callback_data": CallbackData.profile},
            _('inline_back_to_main_menu', self.user['language_code']): {"callback_data": CallbackData.user_home}
        })

        try:
            last_payment_mid = await cache.get(
                CacheData.last_payment_mid.format(self.user['telegram_id'])
            )
            await bot.delete_message(
                chat_id      = self.user['telegram_id'],
                message_id   = last_payment_mid,
            )
        except Exception as e:
            print(e)

        try:
            await bot.send_message(
                chat_id      = self.user['telegram_id'],
                text         = msg,
                reply_markup = kb
            )
        except Exception as e:
            await db.set_raw(
                f"UPDATE users SET is_active = 0 WHERE id = {self.user['id']}"
            )
            logging.warning(f"Пользователь {self. user['telegram_id']} удалил бот, ошибка: {str(e)}")
