# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2024, Павел Зверев

import aiofiles
import os
import uuid

from loader import bot, config as cfg, _, u, root_dir, loop
from utils.logging import logging

IMAGES_DIR = f'{root_dir}/static/'
if not os.path.isdir(IMAGES_DIR):
    os.mkdir(IMAGES_DIR)

def delete_files(
    filenames: list = [],
    dir_path: str  = IMAGES_DIR,
):
    for filename in filenames:
        try:
            os.remove(dir_path + filename)
        except FileNotFoundError as e:
            logging.warning(e)

async def upload_telegram_files(
    files:    list = [],
    dir_path: str  = IMAGES_DIR,
    uid:      int  = 0,
    url:      str  = f"https://{cfg['webhook']['host']}:{cfg['webhook']['port']}/static/"
) -> list:
    """ Загружает файлы по file_id из ТГ

        Возвращает список ссылок
    """
    links = []
    filenames = []

    if not files:
        return links

    for file in files:
        file_info = await bot.get_file(file)
        file = await bot.download_file(file_info.file_path)
        extension = file_info.file_path.split('.')[1]
        filename = f"{uuid.uuid4()}.{extension}"
        async with aiofiles.open(f"{dir_path}/" + filename, "wb") as f:
            await f.write(file)
        links.append(url + filename)
        filenames.append(filename)

    return links, filenames
