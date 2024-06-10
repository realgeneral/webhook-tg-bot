# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import db

async def clear_dialog_data() -> None:
    """ Очищает историю диалогов с dialog_id = 0
    """
    pass
    # await db.set_raw("""
    #     UPDATE requests SET message = '', answer = '' WHERE dialog_id = 0;
    # """)
