# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from telebot.asyncio_handler_backends import State, StatesGroup

class BotState(StatesGroup):
    """Состояния бота в UI"""
    choose_language = State()

    gpt_chat = State()
    new_dialog = State()
    gpt_role = State()

    generate_image = State()

    create_newsletter = State()
    change_limit = State()
    search_user = State()
    add_subscribe = State()

    add_link_newsletter = State()
    search_payment = State()

class CreateDialog(StatesGroup):
    """ Создание диалога
    """
    A1 = State()
    A2 = State()
    A3 = State()

class EditPage(StatesGroup):
    """ Страницы
    """
    A1 = State()
    B1 = State()

class AdminTariffs(StatesGroup):
    """ Тарифы
    """
    A1 = State()
    A2 = State()
    B1 = State()
    B2 = State()
    B3 = State()
    B4 = State()
    B5 = State()

class AdminProvider(StatesGroup):
    """ Провйдеры
    """
    A1 = State()
    A2 = State()

class Shop(StatesGroup):
    """ Магазин
    """
    payment = State()
    promocode = State()

class AdminChatGpt(StatesGroup):
    """ Изменение параметров ChatGPT
    """
    A1 = State()

    # Изменение параметров ChatGPT
    B1 = State()

    # Изменение параметров диалога ChatGPT
    C1 = State()

    # Создание системного диалога
    D1 = State()
    D2 = State()
    D3 = State()

class AdminAffiliate(StatesGroup):
    """ Изменение параметров рефки
    """
    # Изменение параметров
    B1 = State()


class AdminDalle(StatesGroup):
    """ Изменение параметров Dalle
    """
    A1 = State()

class AdminBon(StatesGroup):
    """ Изменение параметров бонусов
    """
    A1 = State()

class AdminStable(StatesGroup):
    """ Изменение параметров Stable Diffusion
    """
    A1 = State()

class AdminMJ(StatesGroup):
    """ Изменение параметров MJ
    """
    A1 = State()

class EditStableParam(StatesGroup):
    """ Изменение параметров Stable Diffusion у пользователя
    """
    A1 = State()

class AdminMj(StatesGroup):
    """ Изменение параметров Midjourney
    """
    A1 = State()

class EditMjParam(StatesGroup):
    """ Изменение параметров Midjourney у пользователя
    """
    A1 = State()

class AdminKeys(StatesGroup):
    """ Ключи
    """
    A1 = State()
    A2 = State()

class AdminUsers(StatesGroup):
    """ Юзеры
    """
    # edit
    A1 = State()

    # param change
    B1 = State()

class AdminPromocodes(StatesGroup):
    """ Промокоды
    """
    # add promocode
    A1 = State()
    A2 = State()
    A3 = State()

class AdminChannels(StatesGroup):
    """ Каналы
    """
    # add channels
    A1 = State()
    A2 = State()

class MidjourneyState(StatesGroup):
    """ Состояния MJ
    """
    A1 = State()
    A2 = State()
