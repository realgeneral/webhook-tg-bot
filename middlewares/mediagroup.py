from telebot.handler_backends import BaseMiddleware
from telebot import TeleBot
from telebot.handler_backends import CancelUpdate, SkipHandler
from telebot.types import CallbackQuery, Message
from loader import bot, _, cache
from utils.strings import CallbackData, CacheData
from utils.logging import logging

import asyncio
import time

class MediaGroupMiddleware(BaseMiddleware):
    album_data = {}

    def __init__(self):
        self.latency = 2.5
        self.update_types = ['message']

    async def pre_process(self, message, data):
        if not message.media_group_id:
            return

        mgid = message.media_group_id

        try:
            self.album_data[mgid].append(message)
            raise CancelUpdate()
        except KeyError:
            self.album_data[mgid] = [message]

            await asyncio.sleep(self.latency)

            self.album_data[f'{mgid}_is_last'] = True
            data['media_group'] = self.album_data[mgid]

            logging.warning(f"Media group _{mgid}_ added")

    async def post_process(self, message, data, exception):
        mgid = message.media_group_id
        if mgid and self.album_data.get(f'{mgid}_is_last'):
            del self.album_data[mgid]
            del self.album_data[f'{mgid}_is_last']
