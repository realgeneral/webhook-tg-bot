# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

import httpx
import openai

from loader import config, cache, db
from utils.strings import CacheData
from openai import AsyncOpenAI

async def chat_completion(
    api_key:           str   = None,
    model:             str   = config['openai']['model'],
    role:              str   = config['openai']['default_role'],
    prompt:            list  = None,
    top_p:             int   = config.getint('openai', 'top_p'),
    max_tokens:        int   = None,
    temperature:       float = config.getfloat('openai', 'temperature'),
    presence_penalty:  float = config.getfloat('openai', 'presence_penalty'),
    frequency_penalty: float = config.getfloat('openai', 'frequency_penalty'),
    request_timeout:   int   = 300
) -> tuple:
    """ Отправляет запрос в OpenAi

        :api_key:           str   API-ключ
        :model:             str   Модель
        :role:              str   Роль
        :prompt:            str   Запрос
        :top_p:             int   Вариативность
        :max_tokens:        int   Ограничение по токенам
        :temperature:       float Температура
        :presence_penalty:  float presence_penalty
        :frequency_penalty: float frequency_penalty

        Возвращает tuple (ответ, использования, ошибки, )
    """
    request = config['openai']['default_answer']
    messages = [{"role": "system", "content": role}]

    if type(prompt) == list:
        messages.extend(prompt)

    if prompt is None:
        messages.append({
            "role": "user",
            "content": config.get('openai', 'default_prompt')
        })

    usage = None
    errors = []

    try:
        base_url = None
        if config.getboolean('openai', 'proxy_endpoint'):
            base_url = config.get('openai', 'proxy_endpoint_url')

        # Proxies
        http_client = None
        if config.getboolean('proxy', 'enabled'):
            http_client = httpx.AsyncClient(
                proxies = {
                    "http://":  config.get('proxy', 'http'),
                    "https://": config.get('proxy', 'http')
                },
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),
            )

        client = AsyncOpenAI(
            api_key=api_key, base_url=base_url,
            http_client=http_client, timeout=request_timeout
        )

        completion = await client.chat.completions.create(
            model             = model,
            messages          = messages,
            top_p             = top_p,
            max_tokens        = max_tokens,
            temperature       = float(temperature),
            presence_penalty  = float(presence_penalty),
            frequency_penalty = float(frequency_penalty)
        )
        usage = {
            'completion_tokens': completion.usage.completion_tokens,
            'prompt_tokens':     completion.usage.prompt_tokens,
            'total_tokens':      completion.usage.total_tokens,
        }
        request = completion.choices[0].message.content
    except openai.APITimeoutError as e:
      errors.extend([
        "TIMEOUT", f"OpenAI API request timed out: {e}"
      ])
    except openai.APIError as e:
      errors.extend([
        "API", f"OpenAI API returned an API Error: {e}"
      ])
    except openai.APIConnectionError as e:
      errors.extend([
        "CONNECTION", f"OpenAI API request failed to connect: {e}"
      ])
    except openai.BadRequestError as e:
      errors.extend(
        ["IVALID_REQUEST", f"OpenAI API request was invalid: {e}"]
      )
    except openai.AuthenticationError as e:
      errors.extend([
        "AUTH", f"OpenAI API request was not authorized: {e}"
      ])
    except openai.PermissionDeniedError as e:
      errors.extend([
        "PERMISSION", f"OpenAI API request was not permitted: {e}"
      ])
    except openai.RateLimitError as e:
      errors.extend([
        "RATE_LIMIT", f"OpenAI API request exceeded rate limit: {e}"
      ])
    except Exception as e:
      errors.extend([
        "OTHER", f"Other error at function chat_completion ({model}): {e}"
      ])

    return request, usage, errors
