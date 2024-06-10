from loader import config

""" Скрипт инициализирует конфигурационный файл
    или недостающие директивы или параметры в них.
"""

# Параметры для инициализации (directive -> param -> value)
params = {
    'default': {
        'token': 'ТОКЕН',
        'debug': False,
        'datetime_mask': '%%Y-%%m-%%d %%H:%%M',
        'unlimited': False,
        'free_tokens': 10000,
        'payment_label': 'BotPayment#{user_id}_{tariff_id}_{datetime}',
        'affiliate': False,
        'affiliate_tokens': 520,
        'affiliate_payment_percent': 12,
        'affiliate_cash_mode': True,
        'support_link': 'https://t.me/',
        'telegram_url': 'https://t.me/',
        'default_undefined_context': 'gpt',
    },
    'service': {
        'gpt': True,
        'dalle': True,
        'midjourney': True,
        'stable_diffusion': True,
    },
    'proxy': {
        'enabled': True,
        'type': 'http',
        'http': 'http://Ttteuf:1py1Yk@46.232.12.65:8000',
        'socks5': None,
    },
    'openai': {
        'added_value_gpt': '0',
        'added_value_speech': '250',
        'animation_text': 'False',
        'dalle_defaul_size': '1024x1024',
        'dalle_max_variants': '1',
        'dalle_request_tokens': '800',
        'dalle_variants': '1',
        'dalle_aspect_ratios': '1024x1024, ',
        'default_answer': 'Привет! Кажется, бот сломался. Мы уже чиним!',
        'default_gpt_dialog_id': '0',
        'default_prompt': 'Специалист, который стремится предоставить наиболее точную и наиболее объемную информацию по запросу.',
        'default_role': '@PremiumAIBot',
        'frequency_penalty': '0.3',
        'gpt4_min_balance': '250',
        'max_custom_gpt_dialogs': '10',
        'max_history_message': '2',
        'max_tokens': '2000',
        'model': 'gpt-3.5-turbo-1106',
        'models': 'gpt-3.5-turbo-1106\n'
                  'gpt-4\n'
                  'gpt-4-1106-preview\n'
                  'gpt-4-vision-preview',
        'presence_penalty': '0.3',
        'proxy_endpoint': 'True',
        'proxy_endpoint_url': 'https://api.proxyapi.ru/openai/v1',
        'save_history': 'True',
        'speech': 'True',
        'temperature': '0.4',
        'top_p': '1',
        'unlimited_models': 'gpt-3.5-turbo-16k-0613,gpt-3.5-turbo,gpt-3.5-turbo-1106, gpt-3.5-turbo-0125'
    },
    'redis': {
        'bot_db': '1',
        'charset': 'utf-8',
        'db': '0',
        'hostname': 'localhost',
        'port': '6379',
        'prefix': 'premiumai_'
     },
    'shop': {
        'admin_email': 'paschazverev@gmail.com',
        'sub_unlimgpt3': 'True',
        'unspent_percent': '2',
     },
     'bonuses': {
        'bonus': '500',
        'min_balance': '1',
        'notification': 'False',
        'status': 'False',
        'time_bonus': '00:06',
        'time_burn_bonus': '23:55'
     },
    'stable_diffusion': {
        'cfg_scale': '7',
        'engine': 'stable-diffusion-xl-1024-v1-0',
        'height': '1024',
        'iti_price': '1500',
        'sampler': 'DDPM',
        'samplers': 'DDIM,DDPM,K_DPMPP_2M,K_DPMPP_2S_ANCESTRAL,K_DPMPP_SDE,K_DPM_2,K_DPM_2_ANCESTRAL,K_EULER,K_EULER_ANCESTRAL,K_LMS',
        'samples': '1',
        'seed': '0',
        'steps': '50',
        'style_preset': 'None',
        'style_presets': 'None,3d-model,analog-film,anime,cinematic,comic-book,digital-art,enhance,fantasy-art,isometric,line-art,low-poly,modeling-compound,neon-punk,origami,photographic,pixel-art,tile-texture',
        'text': 'beaver in space, 3d art',
        'tti_price': '100',
        'width': '1024',
        'aspect_ratios': '16:9,1:1,21:9,2:3,3:2,4:5,5:4,9:16,9:21'
     },
    'subscribe': {
        'channels': 'False',
        'required_subscribe': 'False',
        'unlim_gpt35turbo': 'False',
        'only_one_channel': 'False',
    },
    'webhook': {
        'host': 'musical-engaged-husky.ngrok-free.app',
        'listen': '127.0.0.1',
        'port': '8443',
        'secret_token': 'nS3Zo6AvuwTk9',
        'ssl_priv': 'webhook_pkey.pem',
        'ssl_serv': 'webhook_cert.pem',
        'url': 'https://{0}:{1}/PremiumAiBot'
    },
    'midjourney': {
        'is_send_file': 'True', # text to image
        'tti_price': 20000, # text to image
        'base_upscale_price': 10000, # upscale (U1, U2, U3, U4)
        'mode': 'fast', # relax, fast, turbo
        'fetch': 'polling', # polling, webhook
        'info_link': 'https://s1-brainaid.neuroaibot.ru:8443/static/desc_mj.html', # polling, webhook
        'aspect_ratios': '1:1,2:1,2:3,3:2,4:3,16:9,9:16,6:5',
        'versions': '5.2,6.0',
    },
    'whisper': {
        'formats': 'flac,m4a,mp3,mp4,mpeg,mpga,oga,ogg,wav,webm'
    },
}

for directive in params.keys():
    if directive not in config.sections():
        config.add_section(directive)

    for key, val in params[directive].items():
        if not config[directive].get(key):
            config.set(
                directive, key, str(val)
            )

# После config_update() сохраняет конфигурационные изменения
