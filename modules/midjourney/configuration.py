# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2024, Павел Зверев

import json

from loader import bot, cache, db, config as cfg, _, u, root_dir, bmode

async def midjourney_user_config(user_id):
    """ Инициализирует базовую конфигурацию пользователя
        или возвращает существующую, если она была.

        Данные хранятся в Redis
    """
    default_config = {
        'ratio': '1:1',
        'version': '6.0',
    }

    rkey_config = '{}_midjourney_config'
    data_config = await cache.get(rkey_config.format(user_id))

    if not data_config:
        await cache.set(
            rkey_config.format(user_id),
            json.dumps(default_config)
        )
        data_config = json.dumps(default_config)

    return json.loads(data_config) or default_config

async def midjourney_update_config(user_id, key, val):
    rkey_config = '{}_midjourney_config'
    data_config = await cache.get(rkey_config.format(user_id))
    data_config = json.loads(data_config)
    data_config[key] = val
    await cache.set(
        rkey_config.format(user_id),
        json.dumps(data_config)
    )

    return data_config
