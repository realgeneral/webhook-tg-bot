# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import db, bot, _, config, cache
from keyboards.inline import BotKeyboard
from utils.strings import CallbackData, CacheData
from utils.payment_providers import payment_drivers
from utils.texts import Pluralize
from datetime import datetime, timedelta
from handlers.user.shop import get_tariff_name
from utils.logging import logging
from classes.user import Balance

import asyncio

async def tracking() -> None:
    """ Проверяет оплату и обновляет статус платежей

        Скрипту достаточно обновить статус и отправить уведомление,
        тригер в MySql обновит баланс пользователя самостоятельно.

        Обновление баланса касается статуса "success".
    """
    payments = await db.get_payment({
        'status': 'pending',
        'type': 'tx',
        'close': 0
    })

    # господи прости за TRY, я это поправлю
    try:
        for payment in payments:
            provider = await db.get_payment_provider(
                {'id': payment['payment_provider_id']}
            )

            payment_time = provider[0]['payment_time']

            exp = payment['created_at'] + timedelta(minutes=payment_time)
            now = datetime.now()

            wallet = payment_drivers[provider[0]['slug']](
                api_token=provider[0].get('payment_token'),
                amount=0,
                label=payment['label'],
                tariff=None,
                provider=provider[0]
            )

            payment_exist = await wallet.get_payment(payment['label'])
            balance = Balance(db = db)

            if payment_exist:
                await balance.accept_payment(payment['id'], data = payment_exist)
                continue

            if now > exp:
                await db.update_payment(payment['id'], {'status': 'declined'})
                continue

    except Exception as e:
        logging.warning(e)
