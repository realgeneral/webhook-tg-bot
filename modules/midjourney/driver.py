import re
import io
import aiohttp
import json
import base64
import datetime
import uuid

from loader import config, db, bot, _
from utils.balancing import BalancingKeys
from utils.logging import logging

class MidjourneyGoApi:
    """ Midjourney Driver for goapi.ai
    """
    directive = "midjourney"
    api_host  = 'https://api.midjourneyapi.xyz/mj/v2/{}'

    webhook_endpoint = f"https://{config.get('webhook', 'host')}:{config.get('webhook', 'port')}/midjourney"
    webhook_secret = config.get('webhook', 'secret_token')

    def __init__(self, api_key = None):
        self.balancer = BalancingKeys(self.directive, 50)
        self.api_key = api_key

        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    @staticmethod
    async def upload_files(images = []):
        pass

    async def execute_task(self, task):
        """ Проверка задачи / отправка
        """
        from .handlers import mj_send_image, mj_failed_task

        task_id = task.get('task_id')
        db_task = await db.get_raw(f"""
            SELECT * FROM midjourney_tasks WHERE task_id = "{task_id}" and status = 'pending';
        """)

        if not db_task:
            return False

        db_task = db_task[0]

        if task.get('status') in ['failed']:
            await mj_failed_task(task_id)
            await self.update_task(task, db_task = db_task)
            return True

        if task.get('status') in ['finished']:
            await self.update_task(task, db_task = db_task)
            await mj_send_image(task_id, task.get('task_result').get('image_urls'))
            return True

    async def tracking(self):
        """ Проверка задач в polling (в случае если webhook недоступен)
        """
        from .handlers import mj_send_image, mj_failed_task

        tasks = await db.get_raw("""
            SELECT * FROM midjourney_tasks WHERE status IN ('pending', 'staged', 'processing');
        """)
        for t in tasks:
            task_id = t.get('task_id')
            task = await self.fetch(task_id)

            if task.get('status') in ['failed']:
                await mj_failed_task(task_id)
                await self.update_task(task, db_task = t)

            if task.get('status') in ['finished']:
                await self.update_task(task, db_task = t)
                await mj_send_image(task_id, task.get('task_result').get('image_urls'))

    async def update_task(self, task, db_task = None):
        """ Обновляет таску
        """
        task_result = task.get('task_result')
        task_meta = task.get('meta')

        image_urls = ",".join(task.get('image_urls')) if task.get('image_urls') else ''

        await db.mj_update_task(
            task.get('task_id'),
            {
                'process_mode':   task_meta.get('process_mode'),
                'model_version':  task_meta.get('model_version'),
                'prompt':         task_meta.get('task_param').get('prompt'),
                'image_url':      task_result.get('image_url'),
                'image_urls':     ",".join(task_result.get('image_urls')),
                'retry_count':    task.get('retry_count'),
                'process_time':   task.get('process_time'),
                'status':         task.get('status'),
                'actions':        ",".join(task_result.get('actions')),
                'error_messages': ",".join(
                    task_result.get('error_messages')
                ),
                'data':           json.dumps(
                    task_meta.get('task_request')
                ),
            }
        )

        # try:
        #     image_urls = task_result.get('image_urls')
        #     if db_task and image_urls:
        #         for i in enumerate(image_urls, start = 1):
        #             # Создаём таску в базе
        #             await db.mj_create_task({
        #                 'status':         'finished',
        #                 'task_id':        uuid.uuid4(),
        #                 'origin_task_id': task.get('task_id'),
        #                 'user_id':        db_task.get('user_id'),
        #                 'task_type':      f'upscale{i[0]}',
        #                 'image_url':      i[1],
        #                 'prompt':         task_meta.get('task_param').get('prompt'),
        #                 'tokens':         0,
        #                 'actions':        'high_variation,inpaint,low_variation,outpaint_1.5x,outpaint_2x,outpaint_custom,pan_down,pan_left,pan_right,pan_up,upscale_creative,upscale_subtle',
        #                 'message_data':   db_task.get('message_data'),
        #             })
        # except Exception as e:
        #     logging.warning(e)

    async def fetch(self, task_id):
        """ Получение задачи
        """
        url = self.api_host.format('fetch')
        self.headers['X-API-KEY'] = await self.balancer.get_available_key()

        async with aiohttp.ClientSession() as request:
            data = await request.post(
                url,
                headers=self.headers,
                json={
                    'task_id': task_id
                }
            )
            return await data.json()

    async def prompt_checker(self, prompt):
        url = self.api_host.format('validation')
        print(prompt)
        async with aiohttp.ClientSession() as request:
            data = await request.post(
                url,
                json={
                    'prompt': prompt or 'prompt'
                }
            )
            return await data.json()

    async def task_action(self, **kwargs) -> dict:
        """ Task action
        """
        action = kwargs.get('action')

        url = self.api_host
        data = {
            'origin_task_id': kwargs.get('origin_task_id'),
            'webhook_endpoint': self.webhook_endpoint,
            'webhook_secret': self.webhook_secret,
        }

        if action.startswith('upscale'):
            url = url.format('upscale')
            data.update({
                'index': action.replace('upscale', '').replace('_', '')
            })

        if action.startswith('variation') or action.endswith('variation'):
            url = url.format('variation')
            vary = action if action.endswith('variation') else action.replace('variation', '')
            data.update({
                'index': vary
            })

        if action.startswith('outpaint_'):
            url = url.format('outpaint')
            data.update({
                'zoom_ratio': action.replace('outpaint_', '')
            })

        if action.startswith('pan_'):
            url = url.format('pan')
            data.update({
                'direction': action.replace('pan_', ''),
            })

        if action.startswith('blend'):
            url = url.format('pan')
            data.update({
                'direction': action.replace('pan_', '')
            })

        if action.startswith('retry'):
            url = url.format('reroll')
            data.update({
                'skip_prompt_check': False
            })

        async with aiohttp.ClientSession() as request:
            data = await request.post(
                url,
                headers=self.headers,
                json=data
            )
            return await data.json()

    async def imagine(self, **kwargs) -> dict:
        """ Создание изображения

            :mode: str text-to-image | image-to-image
        """
        mj_conf = kwargs.get('cfg')
        url = self.api_host.format('imagine')

        data = {
            'prompt': kwargs.get('prompt'),
            'skip_prompt_check': True,
            'aspect_ratio': mj_conf.get('ratio'),
            'process_mode': config.get(self.directive, 'mode'),
            'webhook_endpoint': self.webhook_endpoint,
            'webhook_secret': self.webhook_secret,
        }

        if (
            kwargs.get('prompt') and
            any(action in kwargs.get('prompt') for action in ['--aspect', '--ar'])
        ):
            del data['aspect_ratio']

        if (
            kwargs.get('prompt') and
            any(action not in kwargs.get('prompt') for action in ['--version', '--v'])
        ):
            prompt = kwargs.get('prompt') + f" --v {mj_conf.get('version')}"
            data['prompt'] = prompt

        if kwargs.get('mode') and kwargs.get('mode').startswith('blend'):
            url = self.api_host.format('blend')
            data = {
                'prompt': kwargs.get('prompt') or 'blend',
                'image_urls': kwargs.get('photos')[0:5],
                'process_mode': config.get(self.directive, 'mode'),
                'webhook_endpoint': self.webhook_endpoint,
                'webhook_secret': self.webhook_secret,
            }

        async with aiohttp.ClientSession() as request:
            data = await request.post(
                url,
                headers=self.headers,
                json=data
            )
            return await data.json()

    @staticmethod
    def parse_prompt(prompt = 'prompt', lang = 'ru') -> dict:
        prompt = MidjourneyGoApi.replace_static_links_to_html_links(prompt, lang)
        prompt = MidjourneyGoApi.prompt_correction(prompt)

        return prompt

    @staticmethod
    def prompt_correction(prompt) -> dict:
        delete_commands = [
            '--relax', '--fast', '--turbo',
            '—relax', '—fast', '—turbo',
            '—video', '--video',
            '—repeat', '--repeat', '--r', '—r',
        ]
        replace_commands = [
            '—aspect', '—ar',
            '—iw', '—quality', '—q',
            '—style', '—s', '—seed', '—stop',
            '—stylize', '—tile', '—weird',
            '—cref', '—sv', '—sref',
            '—version', '—v', '—chaos',
            '—no', '—niji', '—testp',
        ]

        for command in delete_commands:
            prompt = prompt.replace(command, '')

        for command in replace_commands:
            prompt = prompt.replace(
                command,
                command.replace('—', '--')
            )

        return prompt

    @staticmethod
    def replace_static_links_to_html_links(prompt, lang):
        pattern = r"(https?://\S+)"
        matches = re.findall(pattern, prompt)

        for i, match in enumerate(matches):
            replacement = _('html_link', lang).format(**{
                "match": match,
                "id": i+1
            })
            prompt = prompt.replace(match, replacement)

        return prompt
