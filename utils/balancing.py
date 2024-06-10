# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import db, cache, loop
import logging

# переписать на model -> connections -> token
class BalancingKeys:
    """
    Описание:
        Класс реализует логику управления нагрузкой на ключи OpenAI
        и другие сервисы;

    Аргументы:
        :service:     str сервис;
        :connections: int кол-во активных подключений на ключ;

    Использование:
        1. Перед началом инициализируем ключ self.get_available_key() -> key;
        2. После завершения вызываем self.decrease_connection(key).
    """

    key_list = 'keys:{service}:list'
    key_connections = 'key:{service}:{key}:connections'

    services = ['openai', 'ya_speechkit', 'stable_diffusion', 'midjourney']

    def __init__(
        self,
        service:     str = 'openai',
        connections: int = 500,
        model:       str = 'gpt-3.5-turbo'
    ):
        self.service = service
        self.connections = connections

    async def reset(self) -> None:
        """ Удаляет все ключи

        """
        for service in self.services:
            await cache.delete(self.key_list.format(**{
                'service': service
            }))

    async def load(self) -> list:
        """ Инициализирует список ключей в хранилище

            Returns list
        """
        await self.reset()

        keys = await db.get_key({
            'status': 'active'
        })

        for key in keys:
            await cache.set(self.key_connections.format(**{
                'service': key['service'],
                'key': key['key']
            }), 0)
            await cache.rpush(self.key_list.format(**{
                'service': key['service']
            }), key['key'])

        full_list = {}
        for service in self.services:
            if full_list.get(service) is None:
                full_list[service] = []
            full_list[service].extend(
                await cache.lrange(self.key_list.format(**{
                    'service': service
                }), 0, -1)
            )

        return full_list

    async def create(self, key: str = '') -> str:
        """ Создаёт ключ в хранилище

            :key: str ключ

            Returns int
        """
        await cache.set(self.key_connections.format(**{
            'service': self.service,
            'key': key
        }), 0)

        return await cache.lpush(self.key_list.format(**{
            'service': self.service
        }), key)

    async def get(self, key: str = '') -> str:
        """ Получает кол-во активных соединений у ключа

            :key: str  ключ

            Return str
        """
        return await cache.get(self.key_connections.format(**{
            'service': self.service,
            'key': key
        }))

    async def delete(self, key: str = '') -> int:
        """ Удаляет ключ из хранилища
            и общего списка ключей

            :key: str ключ

            Returns int
        """
        await cache.delete(self.key_connections.format(**{
            'service': self.service,
            'key': key
        }))

        return await cache.lrem(self.key_list.format(**{
            'service': self.service
        }), 0, key)

    async def decrease_connection(self, key: str = '') -> str:
        """ Уменьшает кол-во активных соединений у ключа

            :key: str  ключ

            Return int
        """
        async with cache.pipeline() as pipe:
            key_connections = self.key_connections.format(**{
                'service': self.service,
                'key': key
            })
            await pipe.watch(key_connections)

            pipe.multi()
            await pipe.decr(key_connections)

            await pipe.execute()
            await pipe.unwatch()

            return await cache.get(key_connections)

    async def get_keys(self) -> str:
        """ Получает кол-во активных соединений у всех ключей

            Return dict
        """
        keys = {}
        for key in await cache.lrange(self.key_list.format(**{'service': self.service}), 0, -1):
            keys[key] = await cache.get(self.key_connections.format(**{
                'service': self.service,
                'key': key
            }))

        return keys

    async def get_available_key(self) -> str:
        """ Получает свободный ключ с минимальным кол-вом соединений

            :keys: list список ключей

            Return str
        """
        keys = await cache.lrange(self.key_list.format(**{
            'service': self.service
        }), 0, -1)

        for key in keys:
            async with cache.pipeline() as pipe:
                key_connections = self.key_connections.format(**{
                    'service': self.service,
                    'key': key
                })

                await pipe.watch(key_connections)
                active_connections = int(await pipe.get(key_connections) or 0)

                if active_connections < self.connections:
                    pipe.multi()
                    await pipe.incr(key_connections)
                    await pipe.execute()
                    return key

                await pipe.unwatch()

        return keys[0] if keys else None
