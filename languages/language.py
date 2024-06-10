# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from telebot import types
from .codes import ru, en
import logging
import sys

locales = {}
locales.update(ru.data)
locales.update(en.data)

lang_variants = [l for l in locales.keys()]

async def commands(bot) -> None:
    """ Задаёт список команд для каждого языка

        :bot: класс Telebot
    """
    for variant in lang_variants:
        name = locales.get(variant).get('name')
        commands = locales.get(variant).get('commands')

        # Не добавляет язык, если в словаре отсутствует его название
        # и список команд.
        if name is None or commands is None or type(commands) != dict:
            continue

        commands_list = []
        for k, v in commands.items():
            if k.startswith("+"):
                continue
            commands_list.append(
                types.BotCommand(k, v.replace('\n', '')),
            )

        await bot.set_my_commands(
            commands_list,
            language_code = variant,
            scope         = types.BotCommandScopeAllPrivateChats()
        )

        logging.warning("Команды для языка {0} обновлены".format(name))
