from loader import bot, cache, db, config as cfg, _, loop

import asyncio
import telegram

rkey_message_info = '{cid}_{mid}_{lang_code}_{type}'
rkey_message_info_status = '{cid}_{mid}_{lang_code}_{type}_status'
rkey_message_for_edit_list = 'message_for_edit_list'

expire_time = 180

async def message_add_list(text: str = '', chat_id: int = 0, message_id: int = 0, lang_code: str = 'ru', type: str = 'chatgpt') -> None:
    """ Добавляет сообщение

        :chat_id:
        :message_id:
        :lang_code:
        :type:
    """
    key = rkey_message_info.format(**{'cid': chat_id, 'mid': message_id, 'lang_code': lang_code, 'type': type})
    key_status = rkey_message_info_status.format(**{'cid': chat_id, 'mid': message_id, 'lang_code': lang_code, 'type': type})
    await cache.set(key, text)
    await cache.set(key_status, "0")
    await cache.expire(key, expire_time)
    await cache.rpush(rkey_message_for_edit_list, key)

async def message_remove_list(chat_id: int = 0, message_id: int = 0, lang_code: str = 'ru', type: str = 'chatgpt') -> None:
    """ Удаляет сообщение

        :chat_id:
        :message_id:
        :lang_code:
        :type:
    """
    key = rkey_message_info.format(**{'cid': chat_id, 'mid': message_id, 'lang_code': lang_code, 'type': type})
    key_status = rkey_message_info_status.format(**{'cid': chat_id, 'mid': message_id, 'lang_code': lang_code, 'type': type})
    await cache.lrem(rkey_message_for_edit_list, 0, key)
    await cache.delete(key)
    await cache.delete(key_status)

async def edit_message_task(message):
    """ Обновляет сообщение

        :message: rkey
    """
    emojies = {
        'dalle': {
            0: '‍🌅',
            1: '👨‍🎨'
        },
        'stable': {
            0: '🖌',
            1: '🖼'
        },
        'midjourney': {
            0: '🌉',
            1: '🌆'
        },
        'chatgpt': {
            0: '⌛',
            1: '⏳'
        }
    }

    try:
        message = message.split('_')
        cid, mid, lang_code, type = message

        key_status = rkey_message_info_status.format(**{'cid': cid, 'mid': mid, 'lang_code': lang_code, 'type': type})

        if await cache.get(key_status) == "1":
            return

        key = rkey_message_info.format(**{'cid': cid, 'mid': mid, 'lang_code': lang_code, 'type': type})

        rdata = await cache.get(key)

        await cache.set(key_status, "1")

        if not rdata:
            await message_remove_list(cid, mid, lang_code, type)
            return

        if rdata.startswith(emojies[type][0]):
            rdata = rdata.replace(emojies[type][0], emojies[type][1])
        else:
            rdata = rdata.replace(emojies[type][1], emojies[type][0])

        if type == 'chatgpt':
            await bot.send_chat_action(cid, telegram.constants.ChatAction.TYPING)

        if type in ['dalle', 'stable', 'midjourney']:
            await bot.send_chat_action(cid, telegram.constants.ChatAction.UPLOAD_PHOTO)

        await bot.edit_message_text(
            message_id = mid,
            chat_id    = cid,
            text       = rdata
        )
    except Exception as e:
        await message_remove_list(cid, mid, lang_code, type)
        return

    ttl_key = await cache.ttl(key)
    if ttl_key in [-1, -2]:
        await message_remove_list(cid, mid, lang_code, type)
        return

    if ttl_key > 0:
        await cache.set(key, rdata)
        await cache.expire(key, ttl_key)

    await asyncio.sleep(1)
    await cache.set(key_status, "0")

async def message_edit_loader() -> None:
    """ Таска
    """
    while True:
        try:
            message_list = await cache.lrange(rkey_message_for_edit_list, 0, -1)
            for message in message_list:
                await asyncio.sleep(1.5)
                loop.create_task(edit_message_task(message))
        except Exception as e:
            print(e)

        await asyncio.sleep(0.5)
