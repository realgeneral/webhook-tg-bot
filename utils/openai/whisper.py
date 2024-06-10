import openai
import httpx

from loader import bot, cache, db, config, _
from utils.balancing import BalancingKeys

async def recognize_speech(
    audio_data,
    filename        = 'voice.oga',
    response_format = None
):
    """ Преобразует аудиосообщение в текст
        с помощью Whisper

        :audio_data: ogg файл от Telegram
    """
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
    # Иницализируем класс распределения токенов

    balancer = BalancingKeys(service='openai', connections=50)
    api_key = await balancer.get_available_key()

    transcription = None
    client = openai.AsyncOpenAI(api_key=api_key, http_client=http_client,)

    try:
        transcription = await client.audio.transcriptions.create(
            model           = "whisper-1",
            file            = (filename, audio_data),
            response_format = response_format
        )
    except Exception as e:
        logging.warning(e)

    await balancer.decrease_connection(api_key)

    return getattr(transcription, 'text', None) or transcription
