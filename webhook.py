import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.staticfiles import StaticFiles
from starlette.routing import Mount
from telebot.types import Message, Update
from utils.configurable import config_update

from loader import bot, db, config, root_dir, user_middleware, loop, cache, bmode
from utils.logging import logging
from utils.payment_providers import payment_drivers
from middlewares import antiflood, mediagroup
from telebot import asyncio_filters
from handlers import admin, chat, user
from languages.language import commands
from utils.balancing import BalancingKeys
from utils.misc import bot_username_in_cache
from utils.message_loader import message_edit_loader

import multiprocessing
import announcements
import aiofiles
import filters
import asyncio
import argparse
import os
import sys

bmode = 'webhook'

WEBHOOK_SECRET_TOKEN = config['webhook']['secret_token']
WEBHOOK_HOST         = config['webhook']['host']
WEBHOOK_PORT         = config['webhook']['port']
WEBHOOK_LISTEN       = config['webhook']['listen']
WEBHOOK_SSL_CERT     = config['webhook']['ssl_serv']
WEBHOOK_SSL_PRIV     = config['webhook']['ssl_priv']
WEBHOOK_URL          = config['webhook']['url'].format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_SECRET_TOKEN = config['webhook']['secret_token']

# middlewares
# bot.setup_middleware(mediagroup.MediaGroupMiddleware)
bot.setup_middleware(antiflood.AntiFloodMiddleware(1))
bot.setup_middleware(user_middleware)
bot.setup_middleware(mediagroup.MediaGroupMiddleware())

# filters
bot.add_custom_filter(filters.main_filters.IsSubscription())
bot.add_custom_filter(filters.main_filters.IsAction())
bot.add_custom_filter(filters.main_filters.Service())
bot.add_custom_filter(filters.main_filters.Role())
bot.add_custom_filter(filters.main_filters.IsChat())
bot.add_custom_filter(filters.main_filters.ControlGptDialog())
bot.add_custom_filter(filters.main_filters.Statistics())
bot.add_custom_filter(filters.main_filters.ContinueCommand())
bot.add_custom_filter(asyncio_filters.StateFilter(bot))

async def run_scheduler():
    await announcements.scheduler()

def start_scheduler_in_new_process():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_scheduler())
    finally:
        loop.close()

async def payments(request: Request) -> Response:
    """ Обрабатывает платежи по вебхукам
    """
    payment_method = request.query_params.get('method')
    # ['robokassa'] в будущем заменить payment_drivers
    if payment_method not in ['robokassa', 'payok'] or payment_method is None:
        return Response('Payment method undefined', status_code=404)

    try:
        form_data = await request.form()
        driver = await payment_drivers[payment_method].check_payment(
            dict(form_data)
        )
        return Response(driver)
    except Exception as e:
        logging.warning(e)
        Response('NOTOK')

async def mjhook(request: Request) -> Response:
    """ Обрабатывает MJ hook о готовности изображения
    """
    try:
        if request.headers.get('x-webhook-secret', None) != WEBHOOK_SECRET_TOKEN:
            raise Exception('Webhook secret not valid')

        from modules.midjourney.driver import MidjourneyGoApi

        task = await request.json()
        logging.warning(task)

        driver = MidjourneyGoApi()
        result = await driver.execute_task(task)

        if result is False:
            raise Exception('Task not found or finished')

        return Response('OK')
    except Exception as e:
        logging.warning(e)
        return Response('OK', status_code = 500)


async def load_users(request: Request) -> Response:
    """ Выгружает айди пользователей (для сервисов аналитики)
    """
    return Response('OK')

async def telegram(request: Request) -> Response:
    """ Обрабатывает апдейты от Telegram
    """
    token_header_name = 'X-Telegram-Bot-Api-Secret-Token'

    if request.headers.get(token_header_name) != WEBHOOK_SECRET_TOKEN:
        return PlainTextResponse('Forbidden', status_code=403)

    # await bot.process_new_updates([Update.de_json(await request.json())])

    data = await request.json()
    try:
        asyncio.create_task(
            bot.process_new_updates([Update.de_json(data)])
        )
    except Exception as e:
        logging.warning(e)

    return Response()

async def startup() -> None:
    """ Регистрация веб-хука для уведомлений
    """
    # Сохраняем конфигурацию (если были импортированы новые секции)
    loop.create_task(config_update())
    # Добавляем команды в меню бота
    loop.create_task(commands(bot))
    # Добавляет в кэш данные о ключах (для распредления нагрузки)
    loop.create_task(BalancingKeys().load())

    # Добавляем scheduler из announcements.py в поток
    process = multiprocessing.Process(target=start_scheduler_in_new_process)
    process.start()

    # Добавляем анимацию ожидания ответа
    loop.create_task(message_edit_loader())
    # Добавляем username бота в кэш
    loop.create_task(bot_username_in_cache())

    await bot.delete_webhook()

    webhook_info = await bot.get_webhook_info(30)
    if WEBHOOK_URL != webhook_info.url:
        logging.debug(
            f'Обновил webhook, старый: {webhook_info.url}, новый: {WEBHOOK_URL}'
        )
        if not await bot.set_webhook(
            url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET_TOKEN,
            max_connections=99, drop_pending_updates=True,
            timeout=300,
            # certificate=open(os.path.join(
            #     root_dir,'config/certificates/public.pem'
            # ), 'r')
        ):
            raise RuntimeError('Не удалось установить вебхук')

app = Starlette(
    routes=[
        Route('/PremiumAiBot', telegram, methods=['POST']),
        Route('/payments',     payments, methods=['POST']),
        Route('/load_users',   load_users, methods=['GET']),
        Route('/midjourney',   mjhook,   methods=['POST']),
        Mount('/static',       StaticFiles(directory='static'))
    ],
    on_startup=[startup]
)
