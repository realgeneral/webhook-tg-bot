# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config as cfg, _, u
from modules.aiomoney.wallet import YooMoneyWallet
from utils.logging import logging

import aiohttp
import uuid
import hashlib
import hmac
import json

class YooMoneyPayment:
    def __init__(
        self,
        api_token: str  = '',
        amount:    int  = 0,
        label:     str  = '',
        tariff:    dict = {},
        provider:  dict = {}
    ):
        self.api_token = api_token
        self.amount = amount
        self.label = label
        self.tariff = tariff
        self.provider = provider
        self.wallet = YooMoneyWallet(
            access_token=self.api_token
        )

    def autopayment() -> str:
        return False

    async def get_information(self) -> str:
        """ Получает информацию о счёте
        """
        try:
            return await self.wallet.account_info
        except Exception as e:
            return None

    async def get_payment(self, label) -> str:
        """ Получает информацию о платеже
        """
        try:
            return await self.wallet.check_payment_on_successful(label)
        except Exception as e:
            return None

    async def create_payment_link(self, payment_id = 0) -> str:
        """ Создаёт платёжную ссылку
        """
        try:
            payment = await self.wallet.create_payment_form(
                amount_rub=self.amount,
                unique_label=str(self.label)
            )
            return {
                'link_for_customer': payment.link_for_customer
            }
        except Exception as e:
            return None

class YooKassaPayment:
    # Get methods
    payment_url = "https://api.yookassa.ru/v3/payments/{}"
    me_payment_url = "https://api.yookassa.ru/v3/me"

    # Post methods
    create_payment_url = "https://api.yookassa.ru/v3/payments"
    capture_payment_url = "https://api.yookassa.ru/v3/payments/{}/capture"

    # headers
    headers = {
        'Content-Type': 'application/json'
    }

    def __init__(self, api_token: str = '', amount: int = 0, label: str = '', tariff: dict = {}, provider: dict = {}):
        self.api_token = api_token
        self.amount = amount
        self.label = label
        self.tariff = tariff
        self.provider = provider
        self.wallet = None

    def autopayment() -> str:
        return True

    async def get_information(self) -> str:
        auth = aiohttp.BasicAuth(login=str(self.provider['data']), password=self.api_token)
        self.headers['Idempotence-Key'] = str(uuid.uuid4())
        try:
            async with aiohttp.ClientSession() as session:
                req = await session.get(
                    self.me_payment_url,
                    auth=auth,
                    headers=self.headers
                )

                response = await req.json()

                if response.get('type') == 'error':
                    raise Exception('Token incorrect')

                if response.get('status') and response.get('status') == 'enabled':
                    return True

                return False
        except Exception as e:
            return None

    async def get_payment(self, payment_id) -> str:
        """ Получает информацию о платеже
            через API-интерфейс платёжного провайдера
        """
        auth = aiohttp.BasicAuth(login=str(self.provider['data']), password=self.api_token)
        self.headers['Idempotence-Key'] = str(uuid.uuid4())
        try:
            async with aiohttp.ClientSession() as session:
                req = await session.get(
                    self.payment_url.format(payment_id),
                    auth=auth,
                    headers=self.headers
                )
                response = await req.json()

                if response.get('paid') and response.get('status') == 'succeeded':
                    print(response)
                    return response
        except Exception as e:
            return None

    async def autopayment(self, payment_id = 0) -> str:
        """ Автоплатёж
        """
        data = {
            "amount": {
              "value": self.tariff['amount'],
              "currency": "RUB"
            },
            "confirmation": {
              "type": "redirect",
              "return_url": "https://t.me/{}"
            },
            "receipt": {
              "customer": {
                "email": cfg.get('shop', 'admin_email')
              },
              "items": [
                {
                  "description": self.tariff['name'],
                  "quantity": "1",
                  "amount": {
                    "value": self.tariff['amount'],
                    "currency": "RUB"
                  },
                  "vat_code": "1"
                }
              ]
            },
            "description": self.tariff['name'],
            'save_payment_method': bool(self.provider['autopayments']),
            'capture': True
        }
        self.headers['Idempotence-Key'] = str(uuid.uuid4())

        # Добавляем return_url
        bot_username = await cache.get('bot_username')
        if bot_username:
            data['confirmation']['return_url'] = data['confirmation']['return_url'].format(bot_username)

        auth = aiohttp.BasicAuth(login=str(self.provider['data']), password=self.api_token)
        try:
            async with aiohttp.ClientSession() as session:
                req = await session.post(
                    self.create_payment_url,
                    auth=auth,
                    json=data,
                    headers=self.headers
                )
                response = await req.json()
                if response.get('type') == 'error':
                    raise Exception

                return {
                    'link_for_customer': response['confirmation']['confirmation_url'],
                    'label': response['id']
                }
        except Exception as e:
            return None

    async def create_payment_link(self, payment_id = 0, payment_method_id = None) -> str:
        """ Создаёт платёжную ссылку
        """
        data = {
            "amount": {
              "value": self.tariff['amount'],
              "currency": "RUB"
            },
            "confirmation": {
              "type": "redirect",
              "return_url": "https://t.me/{}"
            },
            "receipt": {
              "customer": {
                "email": cfg.get('shop', 'admin_email')
              },
              "items": [
                {
                  "description": self.tariff['name'],
                  "quantity": "1",
                  "amount": {
                    "value": self.tariff['amount'],
                    "currency": "RUB"
                  },
                  "vat_code": "1"
                }
              ]
            },
            "description": self.tariff['name'],
            'save_payment_method': bool(self.provider['autopayments']),
            'capture': True
        }
        self.headers['Idempotence-Key'] = str(uuid.uuid4())

        # Добавляем return_url
        bot_username = await cache.get('bot_username')
        if bot_username:
            data['confirmation']['return_url'] = data['confirmation']['return_url'].format(bot_username)

        auth = aiohttp.BasicAuth(login=str(self.provider['data']), password=self.api_token)
        try:
            async with aiohttp.ClientSession() as session:
                req = await session.post(
                    self.create_payment_url,
                    auth=auth,
                    json=data,
                    headers=self.headers
                )
                response = await req.json()
                if response.get('type') == 'error':
                    raise Exception

                return {
                    'link_for_customer': response['confirmation']['confirmation_url'],
                    'label': response['id']
                }
        except Exception as e:
            return None

class RobokassaPayment:
    # Get methods
    create_payment_url = "https://auth.robokassa.ru/Merchant/Indexjson.aspx"
    me_payment_url = "https://auth.robokassa.ru/Merchant/Index/"

    # headers
    headers = {
        'Content-Type': 'application/json'
    }

    def __init__(self, api_token: str = None, amount: int = 0, label: str = '', tariff: dict = {}, provider: dict = {}):
        self.api_token = api_token.split(':')
        self.first_password = self.api_token[0]
        self.second_password = self.api_token[1]
        self.amount = amount
        self.label = label
        self.tariff = tariff
        self.provider = provider
        self.wallet = None

    def autopayment() -> str:
        return False

    async def get_information(self) -> str:
        return True

    async def get_payment(self, payment_id) -> str:
        """ Получает информацию о платеже
            через API-интерфейс платёжного провайдера
        """
        p = await db.get_payment({ 'label': payment_id })
        payment_data = p[0]['payment_data']

        if payment_data is not None:
            # payment_data = json.loads(payment_data)
            return payment_data.get('Shp_label') == payment_id

        return None

    @staticmethod
    async def check_payment(data: dict):
        if not data.get('SignatureValue'):
            return None

        provider = await db.get_payment_provider(
            {'slug': 'robokassa'}
        )

        api_token = provider[0]['payment_token'].split(':')
        first_password = api_token[0]
        second_password = api_token[1]

        signature_value = f"{data['OutSum']}:{data['InvId']}:{second_password}:Shp_label={data['Shp_label']}"
        signature_value = hashlib.md5(signature_value.encode()).hexdigest()

        if signature_value.upper() == data['SignatureValue']:
            payment = await db.get_payment({ 'label': data['Shp_label'] })
            if payment[0]['status'] in ['new', 'pending']:
                await db.update_payment(
                    payment[0]['id'],
                    {
                        'payment_data': json.dumps(data)
                    }
                )
            return f"OK{data['InvId']}"

        return "NOTOK"

    async def create_payment_link(self, payment_id = 0) -> str:
        """ Создаёт платёжную ссылку
        """
        bot_username = await cache.get('bot_username')
        data = {
            "MerchantLogin": self.provider['data'],
            "OutSum": self.tariff['amount'],
            "Description": f"{self.tariff['name']} в https:/t.me/{bot_username}",
            "Shp_label": self.label,
            # "IsTest": 1
        }
        signature_value = f"{self.provider['data']}:{self.tariff['amount']}::{self.first_password}:Shp_label={self.label}"
        data['SignatureValue'] = hashlib.md5(signature_value.encode()).hexdigest()

        try:
            async with aiohttp.ClientSession() as session:
                req = await session.post(
                    self.create_payment_url,
                    data=data,
                )
                response = await req.json()

                if response.get('error') and response['error']['code'] is not None:
                    raise Exception

                return {
                    'link_for_customer': f"{self.me_payment_url}{response['invoiceID']}",
                    'label': 0
                }
        except Exception as e:
            logging.warning(e)
            return None


class LavaPayment:
    # Post methods
    wallet_info_url    = "https://api.lava.ru/business/shop/get-balance"
    create_payment_url = "https://api.lava.ru/business/invoice/create"
    info_payment_url   = "https://api.lava.ru/business/invoice/status"

    # headers
    headers = {
        'Accept':       'application/json',
        'Content-Type': 'application/json'
    }

    def __init__(self, api_token: str = '', amount: int = 0, label: str = '', tariff: dict = {}, provider: dict = {}):
        self.api_token = api_token
        self.amount = amount
        self.label = label
        self.tariff = tariff
        self.provider = provider
        self.wallet = None

    def autopayment() -> str:
        return False

    def sign(self, data: dict):
        """ Подписывает транзу
        """
        data = json.dumps(data).encode()
        return  hmac.new(bytes(self.api_token, 'UTF-8'), data, hashlib.sha256).hexdigest()

    async def get_information(self) -> str:
        try:
            data = {
                "shopId": self.provider['data']
            }
            self.headers['Signature'] = self.sign(data)

            async with aiohttp.ClientSession() as session:
                req = await session.post(
                    self.wallet_info_url,
                    headers=self.headers,
                    json=data
                )

                response = await req.json()

                if response.get('status') == 200:
                    return True

                if response.get('status') == 'error':
                    raise Exception(f'Token incorrect; Code: {response.get("code")}')

                return False
        except Exception as e:
            logging.warning(e)
            return None

    async def get_payment(self, payment_id) -> str:
        """ Получает информацию о платеже
            через API-интерфейс платёжного провайдера
        """
        data = {
            "shopId": self.provider['data'],
            "orderId": payment_id
        }
        self.headers['Signature'] = self.sign(data)
        try:
            async with aiohttp.ClientSession() as session:
                req = await session.post(
                    self.info_payment_url,
                    headers=self.headers,
                    json=data
                )
                response = await req.json()
                if response.get('data') and response['data']['status'] == 'success':
                    return True
        except Exception as e:
            logging.warning(e)
            return None

    async def create_payment_link(self, payment_id = 0) -> str:
        """ Создаёт платёжную ссылку
        """
        bot_username = await cache.get('bot_username')

        data = {
            "sum": self.tariff['amount'],
            "orderId": self.label,
            "shopId": self.provider['data'],
            "expire": self.provider['payment_time'],
            "comment": f"{self.tariff['name']} в https:/t.me/{bot_username}",
        }
        self.headers['Signature'] = self.sign(data)

        try:
            async with aiohttp.ClientSession() as session:
                req = await session.post(
                    self.create_payment_url,
                    json=data,
                    headers=self.headers
                )
                response = await req.json()
                if not response.get('data') or response.get('data') == None:
                    raise Exception

                return {
                    'link_for_customer': response['data']['url'],
                    'label': self.label
                    # 'label': response['data']['id']
                }
        except Exception as e:
            return None


class SelfPayment:
    """ Личные платежи
    """
    def __init__(self, api_token: str = '', amount: int = 0, label: str = '', tariff: dict = {}, provider: dict = {}):
        self.api_token = api_token
        self.amount = amount
        self.label = label
        self.tariff = tariff
        self.provider = provider
        self.wallet = None

    def autopayment() -> str:
        return False

    async def get_information(self) -> str:
        return True

    async def get_payment(self, payment_id) -> str:
        """ Получает информацию о платеже
            через API-интерфейс платёжного провайдера
        """
        return None

    async def create_payment_link(self, payment_id = 0) -> str:
        """ Создаёт платёжную ссылку
        """
        return {
            'link_for_customer': self.provider['data'],
            'extra_info_string_key': 'extra_info_self_payment'
        }

class PayOkPayment:
    # Get methods
    create_payment_url = "https://payok.io/pay"
    me_payment_url = "https://auth.robokassa.ru/Merchant/Index/"

    # headers
    headers = {
        'Content-Type': 'application/json'
    }

    def __init__(self, api_token: str = None, amount: int = 0, label: str = '', tariff: dict = {}, provider: dict = {}):
        self.api_token = api_token.split(':')
        self.amount = amount
        self.label = label
        self.tariff = tariff
        self.provider = provider
        self.wallet = None

    def autopayment() -> str:
        return False

    async def get_information(self) -> str:
        return True

    async def get_payment(self, payment_id) -> str:
        """ Получает информацию о платеже
            через API-интерфейс платёжного провайдера
        """
        p = await db.get_payment({ 'label': payment_id })
        payment_data = p[0]['payment_data']

        if payment_data is not None:
            # payment_data = json.loads(payment_data)
            return str(p[0]['id']) in str(payment_data)

        return None

    @staticmethod
    async def check_payment(data: dict):
        if not data.get('sign'):
            return None

        provider = await db.get_payment_provider(
            {'slug': 'payok'}
        )

        api_token = provider[0]['payment_token']

        signature_value = f"{api_token}|{data['desc']}|{data['currency']}|{data['shop']}|{data['payment_id']}|{data['amount']}"
        signature_value = hashlib.md5(signature_value.encode()).hexdigest()

        if signature_value == data['sign']:
            payment = await db.get_payment({ 'id': data['payment_id'] })
            if payment[0]['status'] in ['new', 'pending']:
                await db.update_payment(
                    payment[0]['id'],
                    {
                        'payment_data': json.dumps(data['payment_id'])
                    }
                )
            return "OK"

        return "NOTOK"

    async def create_payment_link(self, payment_id = 0) -> str:
        """ Создаёт платёжную ссылку
        """
        bot_username = await cache.get('bot_username')

        data = {
            "amount": self.tariff['amount'],
            "payment": payment_id,
            "shop": self.provider['data'],
            "currency": 'RUB',
            "desc": f"{self.tariff['tokens']:,} tokenov",
            "secret": self.provider['payment_token']
        }

        signature_value = "|".join(map(str, data.values()))
        data['sign'] = hashlib.md5(signature_value.encode()).hexdigest()

        del data['secret']

        url_params = "&".join([
            f"{i[0]}={i[1]}" for i in data.items()
        ])
        url = "{0}?{1}".format(self.create_payment_url, url_params)

        try:
            async with aiohttp.ClientSession() as session:
                req = await session.get(
                    self.create_payment_url,
                    params=list(data.items()),
                )

                if req.status != 200:
                    raise Exception

                return {
                    'link_for_customer': url,
                    'label': 0
                }
        except Exception as e:
            logging.warning(e)
            return None

# Платёжные драйверы
payment_drivers = {
    'yoomoney': YooMoneyPayment,
    'yookassa': YooKassaPayment,
    'robokassa': RobokassaPayment,
    'lava': LavaPayment,
    'payok': PayOkPayment,
    'self': SelfPayment,
}
