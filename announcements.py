#
# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2022, Павел Зверев

import datetime as dt
from loader import config
from utils.logging import logging

import asyncio
from tasks import payments_tracking, clear_data, bonuses, tokens
import aioschedule as schedule

async def scheduler():

    try:
        from modules.midjourney.driver import MidjourneyGoApi
        schedule.every(15).seconds.do(MidjourneyGoApi().tracking)
    except ImportError as e:
        logging.warning(e)

    schedule.every(30).seconds.do(payments_tracking.tracking)
    schedule.every(1).minutes.do(tokens.subscription)

    schedule.every().day.at(config.get('bonuses', 'time_bonus')).do(bonuses.bonus_accrual)
    schedule.every().day.at(config.get('bonuses', 'time_burn_bonus')).do(bonuses.bonus_burn)

    while True:
        try:
            await schedule.run_pending()
            await asyncio.sleep(1)
        except Exception as e:
            logging.warning(e)
