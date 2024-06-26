from telebot.handler_backends import BaseMiddleware
from telebot import TeleBot
from telebot.handler_backends import CancelUpdate, SkipHandler
from telebot.types import CallbackQuery, Message
from loader import bot, _, cache
from utils.strings import CallbackData, CacheData

class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit) -> None:
        self.last_time = {}
        self.limit = limit
        self.update_types = ['message']
        # Always specify update types, otherwise middlewares won't work

    async def pre_process(self, message, data):
        # if type(message) == CallbackQuery:
        #     message = message.message

        if not message.from_user.id in self.last_time:
            # User is not in a dict, so lets add and cancel this function
            self.last_time[message.from_user.id] = message.date
            return

        if message.date - self.last_time[message.from_user.id] < self.limit:
            await cache.set(CacheData.stop_next_handler.format(
                message.from_user.id
            ), 0)

        self.last_time[message.from_user.id] = message.date


    async def post_process(self, message, data, exception):
        ...
