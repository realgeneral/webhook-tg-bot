# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

import os
import sys
import telebot
import asyncio
import aioredis
import configparser

from telebot.async_telebot import AsyncTeleBot
from middlewares.user import UserBaseMiddleware
from db.database import Database

# Версия
__version__ = '1.6.0'

# Режим работы
bmode = 'polling'

# Цикл событий
loop = asyncio.get_event_loop()

# Директория запуска приложения
root_dir = os.path.dirname(os.path.abspath(__file__))

# Путь к конфигурации приложения
config_path = os.path.join(root_dir, './config/main.ini')

# Инициализируем конфигурацию
config = configparser.ConfigParser()
config.read(config_path)

import init_config

# База данных
db = Database(
    host     = config.get('mysql', 'hostname'),
    user     = config.get('mysql', 'user'),
    password = config.get('mysql', 'password'),
    db       = config.get('mysql', 'db'),
)

# Redis
cache = aioredis.Redis(
    host             = config.get('redis', 'hostname'),
    port             = config.get('redis', 'port'),
    db               = config.get('redis', 'db'),
    decode_responses = True
)

# Хранилище состояний бота в RedisStorage
state_storage = telebot.asyncio_storage.StateRedisStorage(
    host   = config.get('redis', 'hostname'),
    port   = config.get('redis', 'port'),
    db     = config.get('redis', 'bot_db'), # bot_db for RedisStorage
    prefix = config.get('redis', 'prefix')
)

# Инициализация бота
bot = AsyncTeleBot(
    token                    = config.get('default', 'token'),
    state_storage            = state_storage,
    parse_mode               = "Markdown",
    disable_web_page_preview = True
)

# Инициализируем пользовательский middleware
user_middleware = UserBaseMiddleware(bot, db, config, cache)

# Язык пользователя для вызова _('key_string')
_ = user_middleware.translate # функция с contextvars для получения перевода

# Пользователь для вызова u.get()
u = user_middleware.user # contextvars для пользователя
