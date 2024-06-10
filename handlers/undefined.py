# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, _, config, u, cache
from utils.openai import chatgpt
from keyboards.inline import BotKeyboard
from utils.subscriptions import check_subscription
from utils.strings import CallbackData, CacheData
from utils.configurable import get_lock

@bot.message_handler(is_chat=False, content_types=['text', 'voice', 'photo', 'video', 'sticker', 'document', 'video_note', 'audio', 'location', 'contact', 'animation'], func=lambda message: True, is_action=True, is_subscription=True)
async def undefined(message, data):
    """ Undefined context
    """
    user = u.get()

    string_back_to = _('inline_back_to_main_menu')

    commands = _('commands')
    commands_to_string = "".join(
        [f"{k.replace('+', '')} - {v}\n" for k, v in commands.items()]
    )

    msg = _('context_undefined').format(**{
        "commands": commands_to_string
    })
    kb = BotKeyboard.smart({
        string_back_to: {'callback_data': CallbackData.user_home}
    })

    if message.text == _('reply_end_dialog') or message.text == _('reply_dialog_clear'):
        await bot.send_message(
            chat_id=message.from_user.id,
            text=msg,
            reply_markup = BotKeyboard.remove_reply()
        )
        return

    # Вынести главные контроллеры в отдельный словарь
    if not data.get('media_group') and message.content_type in ['photo', 'text'] and config.get('default', 'default_undefined_context') == 'gpt':
        lock = await get_lock(message.from_user.id)

        gpt_lock_key = CacheData.chatgpt_generation.format(message.from_user.id)
        gpt_lock = await cache.get(gpt_lock_key)

        if gpt_lock:
            await bot.send_message(
                chat_id = message.from_user.id,
                text    = _('gpt_locked_request')
            )
            return

        async with lock:
            await cache.set(gpt_lock_key, 0)
            await cache.expire(gpt_lock_key, 30)

            image = None
            if message.content_type == 'photo':
                image = message.photo[-1]
                image = await bot.get_file(image.file_id)
                image = await bot.download_file(image.file_path)
                message.text = message.caption if message.caption else _('describe_photo')

            await chatgpt.chatgpt(
                data['user'],
                {
                    'message_id': message.message_id,
                    'from_user_id': message.from_user.id,
                    'chat_id': message.chat.id,
                    'text': message.text,
                    'content_type': message.content_type,
                    'image': image
                }
            )

        await cache.delete(gpt_lock_key)

        return

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        parse_mode   = "Markdown",
        reply_markup = kb
    )
