# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config, _
from telebot.types import Message, CallbackQuery
from keyboards.inline import BotKeyboard

async def check_subscription(user, msg, action: bool = True):
    """ Проверяет и выводит сообщение о том, что
        необходимо подписаться на канал

       :user:
       :message:
       :action:
    """
    lang = user['language_code'] # на случай если пользователь меняет язык

    is_subscribed = True
    channels_subscribed = []

    redis_key_is_subscribe = f"{msg['from_user_id']}_is_subscribe"
    redis_user_subscribe = await cache.get(redis_key_is_subscribe)

    if redis_user_subscribe is None:
        channels = config['subscribe']['channels'].split("\n")
        for channel in channels:
            try:
               channel = channel.split("|")
               chat_member = await bot.get_chat_member(channel[0], msg['from_user_id'])

               is_subscribed = chat_member.status == 'member' or chat_member.status == 'administrator' or chat_member.status == 'creator'
               channels_subscribed.append(is_subscribed)
            except Exception as e:
                # В случае если возникла ошибка, мы пропускаем пользователя
                # Важнее приобрести пользователя, чем потерять его из-за того
                # что в канал/группу не был добавлен бот для проверки
               # is_subscribed = True
               print(e)

        if (
            config.getboolean('subscribe', 'only_one_channel') is False and \
            False not in channels_subscribed or \
            config.getboolean('subscribe', 'only_one_channel') and \
            True in channels_subscribed
        ):
            # Создаём в кэше строку о том, что пользователь был подписан
            # И что следующая проверка будет через n-минут
            await cache.set(redis_key_is_subscribe, 1)
            await cache.expire(redis_key_is_subscribe, 60)

    if config.getboolean('subscribe', 'only_one_channel') is False and False in channels_subscribed:
        is_subscribed = False

    if config.getboolean('subscribe', 'only_one_channel') and True in channels_subscribed:
        is_subscribed = True

    if action:
        promotion_text = _('promotion_text', lang)
        if config.getboolean('subscribe', 'only_one_channel'):
            promotion_text += _('promotion_text_only_one_channel')

        if type(message) == CallbackQuery:
            await bot.edit_message_text(
                chat_id      = msg['from_user_id'],
                message_id   = msg['message_id'],
                text         = promotion_text,
                parse_mode   = "Markdown",
                reply_markup = BotKeyboard.subscribe_channel(lang)
            )

        if type(message) == Message:
            await bot.send_message(
                chat_id      = msg['chat_id'],
                text         = promotion_text,
                parse_mode   = "Markdown",
                reply_markup = BotKeyboard.subscribe_channel(lang)
            )

    return is_subscribed


async def is_chat_exist(message: Message):
    """Проверяет зарегистрирован ли чат в боте
    """
    telegram_chat_id = message.chat.id
    chat = await db.get_user(telegram_chat_id, type="chat")

    # Если чат не существует, создаём
    if chat is None:
        await db.create_user(
            message.chat.id,
            username=message.chat.id or _('neurouser'),
            lang='ru',
            type='chat',
            balance=config.get('default', 'free_tokens')
        )
        chat = await db.get_user(message.chat.id, type='chat')

    await bot.reply_to(
        message,
        f'🙋 *Привет!*\n\nChat ID: `{message.chat.id}`\nБаланс: *{chat["balance"]} токенов*\n\nВ чате доступна команда /gpt.\n\n**/gpt** _ваш запрос_ \n_ChatGPT ответит на любой ваш вопрос._\n\n',
        parse_mode="Markdown"
    )

    return True
