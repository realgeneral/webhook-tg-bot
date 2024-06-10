# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2022, Павел Зверев

from loader import bot, db, config, root_dir, user_middleware, loop
from middlewares import antiflood, mediagroup
from telebot import asyncio_filters
from handlers import admin, chat, user
from languages.language import commands
from utils import logging
from utils.balancing import BalancingKeys
from utils.misc import bot_username_in_cache
from utils.message_loader import message_edit_loader
from utils.configurable import config_update

import multiprocessing
import announcements
import filters
import asyncio
import argparse
import os
import sys

# middlewares
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

if __name__ == "__main__":
    # Добавляю команды
    command = argparse.ArgumentParser()
    command.add_argument('-db', help='Импортирование существующей базы данных'
                                     'из файла ./data/gpt.sql')

    args = command.parse_args()
    if args.db == 'import':
        asyncio.run(db.create_structure(root_dir))
        sys.exit()

    # Сохраняем конфигурацию (если были импортированы новые секции)
    loop.create_task(config_update())

    # Добавляем команды в меню бота
    loop.create_task(commands(bot))

    # Добавляет в кэш данные о ключах (для распредления нагрузки на ключи)
    loop.create_task(BalancingKeys().load())

    # Добавляем анимацию ожидания ответа
    loop.create_task(message_edit_loader())

    # Добавляем username бота в кэш
    loop.create_task(bot_username_in_cache())

    # Добавляем scheduler из announcements.py в поток
    process = multiprocessing.Process(target=start_scheduler_in_new_process)
    process.start()

    # For console
    print('OK')

    # Запускаем бота
    loop.run_until_complete(bot.infinity_polling(
        restart_on_change=config.getboolean('default', 'debug')
    ))
