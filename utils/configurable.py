from loader import config, loop, config_path
import asyncio

user_locks = {}

async def get_lock(user_id):
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]

def update_config_file() -> bool:
    """ Обновляет конфиг

        ...config.set...
        ...update = await loop.run_in_executor(None, update_config_file)...
    """
    with open(config_path, 'w') as file:
        config.write(file)

async def config_update():
    await loop.run_in_executor(None, update_config_file)
