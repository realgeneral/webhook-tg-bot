from loader import config
from utils.balancing import BalancingKeys
import aiohttp
import json
import base64

from PIL import Image
import io

from PIL import Image

async def resize_image(data, width, height):
    """ Изменяет размер изображения

        :data:
        :width:
        :height:
    """
    image = Image.open(io.BytesIO(data))

    resized_image = image.resize((width, height))

    output = io.BytesIO()
    resized_image.save(output, format='JPEG')
    resized_data = output.getvalue()

    return resized_data

class StableDiffusion:
    directive = "stable_diffusion"
    api_host  = "https://api.stability.ai/"

    engine_core = 'stable_core'
    stable_three = ['sd3', 'sd3-turbo']

    def __init__(self, api_key):
        self.api_key = api_key
        self.engine =  config.get(self.directive, 'engine')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def image_create(self, **kwargs) -> dict:
        """ Создание изображения

            :mode: str text-to-image | image-to-image
        """
        # Parameters
        path = None

        j = {
            "text_prompts": [
                {
                    "text": kwargs.get(
                        'text',
                        config.get(self.directive, 'text')
                    )
                }
            ],
            "cfg_scale": kwargs.get(
                'cfg_scale',
                config.getint(self.directive, 'cfg_scale')
            ),
            "seed": kwargs.get(
                'seed',
                config.getint(self.directive, 'seed')
            ),
            "steps": kwargs.get(
                'steps',
                config.getint(self.directive, 'steps')
            ),
            "samples": kwargs.get(
                'samples',
                config.getint(self.directive, 'samples')
            ),
            "sampler": kwargs.get(
                'sampler',
                config.get(self.directive, 'sampler')
            ),
        }

        if self.engine == self.engine_core:
            path = 'v2beta/stable-image/generate/core'
            j = {
                'prompt': kwargs.get(
                    'text',
                    config.get(self.directive, 'text')
                ),
                'aspect_ratio': kwargs.get(
                    'aspect_ratio',
                    '1:1'
                 ),
                'seed': kwargs.get(
                    'seed',
                    0
                 ),
                'output_format': kwargs.get(
                    'output_format',
                    'jpeg'
                 ),
            }

        if self.engine in self.stable_three:
            path = 'v2beta/stable-image/generate/sd3'
            j = {
                'prompt': kwargs.get(
                    'text',
                    config.get(self.directive, 'text')
                ),
                'aspect_ratio': kwargs.get(
                    'aspect_ratio',
                    '1:1'
                 ),
                'seed': kwargs.get(
                    'seed',
                    0
                 ),
                'output_format': kwargs.get(
                    'output_format',
                    'jpeg'
                 ),
                'model': self.engine,
                'mode': kwargs.get('mode', 'image-to-image')
            }

        if (
            self.engine not in self.stable_three and
            kwargs.get('style_preset') and
            kwargs.get('style_preset') != 'None'
        ):
            j.update({
                "style_preset": kwargs.get(
                    'style_preset',
                    config.get(self.directive, 'style_preset')
                ),
            })

        if self.engine != self.engine_core and self.engine not in self.stable_three and kwargs.get('mode', None) == 'image-to-image':
            # Удаляем основу
            del j['prompt']
            # Добавляем новый формат промпта для multipart/form-data
            j['text_prompts[0][text]'] = kwargs.get(
                'text',
                config.get(self.directive, 'text')
            )
            # Добавляем вес (нужно сделать незаметный парсер из текста)
            j['text_prompts[0][weight]'] = '0.5'

            j['init_image'] = kwargs.get('init_image')

            return await self.image_to_image(j)

        if self.engine in self.stable_three and kwargs.get('mode', None) == 'image-to-image':
            del j['aspect_ratio']

            j['strength'] = "0.6"
            j['image'] = kwargs.get('init_image')

            return await self.new_image_to_image(j)

        return await self.new_text_to_image(j, path) if self.engine == self.engine_core or self.engine in self.stable_three else await self.text_to_image(j)

    async def new_text_to_image(self, data, path = 'v2beta/stable-image/generate/core') -> dict:
        url = f"{self.api_host}{path}"

        del self.headers['Content-Type']
        self.headers['Accept'] = f"application/json; type=image/{data['output_format']}"

        d = aiohttp.FormData()
        for k, v in data.items():
            d.add_field(
                str(k), str(v)
            )
        d.add_field('file', b'\x00', filename='image.jpeg', content_type='image/jpeg')

        async with aiohttp.ClientSession() as session:
            r = await session.post(
                url,
                headers=self.headers,
                data=d,
            )
            return await r.json()

    async def text_to_image(self, data) -> dict:
        """ Текст в картинку (с промптом)
        """
        url  = f"{self.api_host}v1/generation/{self.engine}/text-to-image"

        async with aiohttp.ClientSession() as session:
            r = await session.post(
                url, headers=self.headers,
                json=data
            )
            return await r.json()

    async def new_image_to_image(self, data) -> dict:
        """ Картинку в картинку (с промптом)
        """
        del self.headers['Content-Type']
        self.headers['Accept'] = f"application/json; type=image/{data['output_format']}"

        url = f"{self.api_host}v2beta/stable-image/generate/sd3"

        d = aiohttp.FormData()
        for k, v in data.items():
            if k == 'image':
                v = await resize_image(v, 1024, 1024)
                d.add_field(
                    k, v
                )
                continue
            d.add_field(
                str(k), str(v)
            )

        async with aiohttp.ClientSession() as session:
            r = await session.post(
                url, headers=self.headers,
                data=d,
            )
            print(await r.json())
            return await r.json()

    async def image_to_image(self, data) -> dict:
        """ Картинку в картинку (с промптом)
        """
        del self.headers['Content-Type']
        url = f"{self.api_host}v1/generation/{self.engine}/image-to-image"

        d = aiohttp.FormData()
        for k, v in data.items():
            if k == 'init_image':
                v = await resize_image(v, 1024, 1024)
                d.add_field(
                    k, v
                )
                continue
            d.add_field(
                str(k), str(v)
            )

        async with aiohttp.ClientSession() as session:
            r = await session.post(
                url, headers=self.headers,
                data=d,
            )
            return await r.json()

    async def balance(self):
        """ Получает баланс кредитов на аккаунте
        """
        url = f"{self.api_host}/user/balance"
        async with aiohttp.ClientSession() as session:
            r = await session.get(url, headers=self.headers)
            return await r.json()
