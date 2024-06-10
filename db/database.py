# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from aiomysql import connect
from aiomysql.cursors import SSCursor, DeserializationCursor, DictCursor
from datetime import datetime
from telebot.formatting import escape_markdown
import json
import sys

# TODO: перевод на sqlalchemy / или избавиться от дубликатов

class Database():
    def __init__(self, host, user, password, db):
        self.host=host
        self.user=user
        self.password=password
        self.db=db

    async def connect(self):
        """ Подключение
        """
        return await connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db,
            charset='utf8',
            use_unicode=True
        )

    async def create_structure(self, root_dir):
        """ Импортирование базы данных
        """
        async with await self.connect() as connection:
            try:
                async with connection.cursor() as cursor:
                    # Открываем/читаем/закрываем файл
                    sql_file = open(root_dir + '/data/sql/gpt.sql', encoding='utf-8')
                    sql_data = sql_file.read()
                    sql_file.close()

                    # Разбиваем на команды
                    sql_lines = sql_data.split(';')

                    # Добавляем команды в запрос
                    for line in sql_lines:
                        if line.rstrip() != '':
                            await cursor.execute(line)

                # Отправляем транзакцию
                await connection.commit()

                print("База данных успешно импортирована.")

            except Warning as warn:
                print('Ошибка: %s ' % warn)
                sys.exit()

    @staticmethod
    def update_format(sql, parameters: dict, sep=", "):
        if "XXX" not in sql: sql += " XXX "

        if parameters == {}:
            sql = ""

        values = f"{sep} ".join([
            f"{k} = %s" for k in parameters
        ])
        sql = sql.replace("XXX", values)

        return sql, tuple(parameters.values())

    async def get_config(self):
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM config"""
                    await cursor.execute(sql)
                    return await cursor.fetchone()

    async def update_config(self, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE config {sql}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def get_subscription(self, user_id, is_active=1):
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM subscriptions WHERE user_id = {user_id} AND is_active = {is_active} ORDER BY id DESC LIMIT 0, 1"""
                    await cursor.execute(sql)
                    return await cursor.fetchone()

    async def update_subscription(self, user_id, id, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE subscriptions {sql} WHERE user_id = {user_id} AND id = {id}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def create_request(self, user_id, dialog_id, type, message, answer, prompt_tokens=0, completion_tokens=0, total_tokens=0, unlimited=0, request_type='text', is_sub = 1, status = 'success'):
        async with await self.connect() as connection:
            sql = f"""
             INSERT INTO requests (user_id, dialog_id, type, message, answer, prompt_tokens, completion_tokens, total_tokens, unlimited, request_type, is_sub, status, created_at)
             VALUES
                 (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, (user_id, dialog_id, type, message, answer, prompt_tokens, completion_tokens, total_tokens, unlimited, request_type, is_sub, status, datetime.now()))
                await connection.commit()
                return await cursor.fetchone()

    async def create_dialog(
        self,
        user_id,
        title,
        role='ChatGPT',
        top_p = 0,
        max_tokens = 0,
        temperature = 0,
        presence_penalty = 0,
        frequency_penalty = 0,
        count_history_messages = 0,
        is_system = 0,
        model='gpt-3.5-turbo-0613',
    ) -> int:
        async with await self.connect() as connection:
            sql = f"""
             INSERT INTO dialogs (user_id, title, role, top_p, max_tokens, temperature, presence_penalty, frequency_penalty, count_history_messages, is_system, model,  created_at)
             VALUES
                 (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, (
                    user_id, title, role, top_p, max_tokens,
                    temperature, presence_penalty, frequency_penalty,
                    count_history_messages, is_system, model,
                    datetime.now()
                ))
                await connection.commit()
                return cursor.lastrowid

    async def update_dialog(self, user_id = 0, dialog_id = 0, args: dict = {}):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE dialogs {sql} WHERE id = {dialog_id}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def get_dialog(self, args={}, order='ASC', start_limit=0, end_limit=25):
        """ Получает диалг/диалоги

        """
        sql, params = self.update_format("WHERE", args, sep=" AND ")
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM `dialogs` {sql} ORDER BY id {order} LIMIT {start_limit}, {end_limit}"""
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()

    # MIGRATE to get_dialog
    async def get_dialogs(self, user_id, is_active=1):
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM dialogs WHERE user_id = {user_id} AND is_active = {is_active} AND is_system=0"""
                    await cursor.execute(sql)
                    return await cursor.fetchall()

    # MIGRATE to get_dialog
    async def get_system_dialogs(self, is_active=1, lang_code='ru'):
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM dialogs WHERE is_system=1 AND is_active = {is_active} AND language_code='{lang_code}'"""
                    await cursor.execute(sql)
                    return await cursor.fetchall()

    async def get_all_users(self, type='user'):
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM users WHERE type = '{type}'"""
                    await cursor.execute(sql)
                    return await cursor.fetchall()

    async def get_user(self, user_id, name_id="telegram_id", type='user', additional_sql=""):
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM users WHERE {name_id} = '{user_id}' AND type = '{type}' {additional_sql}"""
                    await cursor.execute(sql)
                    return await cursor.fetchone()

    async def get_requests(self, user_id, dialog_id, limit=6):
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM requests WHERE user_id = {user_id} AND dialog_id = {dialog_id} AND is_deleted = 0 ORDER BY id DESC LIMIT 0, {limit}"""
                    print(sql)
                    await cursor.execute(sql)
                    return await cursor.fetchall()

    async def get_chat_or_user(self, data):
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM users WHERE telegram_id = %s OR username = %s"""
                    await cursor.execute(sql, (data, data))
                    return await cursor.fetchone()

    async def create_user(self, telegram_id, username, balance=0, reffer_id=0, lang='nill', type='user'):
        async with await self.connect() as connection:
            sql = f"""
             INSERT INTO users (telegram_id, reffer_id, language_code, type, username, balance, billing_information, is_active, created_at)
             VALUES
                 ({telegram_id}, {reffer_id}, '{lang}', '{type}', "{username}", {balance}, 0, 1, "{datetime.now()}")
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql)
                await connection.commit()
                return cursor.lastrowid

    async def create_subscription(self, user_id, expires_at, is_active=1, request_per_day_limit=0):
        async with await self.connect() as connection:
            sql = f"""
             INSERT INTO subscriptions (user_id, request_per_day_limit, is_active, expires_at, created_at) VALUES ({user_id}, {request_per_day_limit}, {is_active}, "{expires_at}", "{datetime.now()}")
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql)
                await connection.commit()

    async def update_user(self, user: int, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE users {sql} WHERE telegram_id = {user}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def get_count(self, table="users", q={"type": "user"}):
        """ Кол-во строк в таблице

        """
        sql, params = self.update_format("WHERE", q, sep=" AND")
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT COUNT(*) as count FROM {table} {sql}"""
                    await cursor.execute(sql, params)
                    res = await cursor.fetchone()
                    return res['count']

    async def history_clear(self, dialog_id=0):
        """ Очищает историю чата

            :dialog_id:
        """
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor) as cursor:
                    sql = f"""UPDATE requests SET message='', answer='', is_deleted=1 WHERE dialog_id={dialog_id}"""
                    await cursor.execute(sql)
                    await connection.commit()


    async def get_pages(self, args={}, start_limit=0, end_limit=50):
        """ Получает список всех страниц

            :start_limit: int
            :end_limit:   int
        """
        sql, params = self.update_format("WHERE", args, sep=" AND ")
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM pages {sql} LIMIT {start_limit}, {end_limit}"""
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()

    async def get_spent_tokens(self, user_id):
        """ Получает кол-во всех потраченных токенов

        """
        async with await self.connect() as connection:
            async with connection.cursor(DeserializationCursor, DictCursor) as cursor:
                    # sql = f"""SELECT type, SUM(total_tokens) FROM requests WHERE user_id={user_id} GROUP by type"""
                    sql = f"""SELECT COALESCE(SUM(total_tokens), 0) AS total_tokens FROM requests WHERE user_id={user_id}"""
                    await cursor.execute(sql)
                    return await cursor.fetchone()

    async def get_page(self, args):
        """ Получает данные о странице

            :slug:    int|str идентификатор/ссылка страницы
            :name_id: str тип идентификатора (slug/id)
        """
        sql, params = self.update_format("WHERE", args, sep=" AND ")
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM pages {sql}"""
                    await cursor.execute(sql, params)
                    return await cursor.fetchone()

    async def update_page(self, page_id=1, name_id="id", args: dict = {}):
        """ Обновляем данные о странице

            :page_id: int  идентификатор страницы
            :name_id: str  тип идентификатора
            :args:    dict словарь с данными для обновления
        """
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE pages {sql} WHERE {name_id} = {page_id}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def get_tariff(self, args):
        """ Получает тариф/тарифы

        """
        sql, params = self.update_format("WHERE", args, sep=" AND ")
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM tariffs {sql}"""
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()


    async def update_tariff(self, id: str, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE `tariffs` {sql} WHERE `id` = '{id}'
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()


    async def create_tariff(self, args={}):
        async with await self.connect() as connection:
            data = {
                'user_id':             args.get('user_id', 0),
                'language_code':       args.get('language_code', 'ru'),
                'name':                args.get('name', args.get('tokens', 0)),
                'tokens':              args.get('tokens', 0),
                'amount':              args.get('amount', 0),
                'currency':            args.get('currency', 'rub'),
                'status':              args.get('status', 'active'),
                'created_at':          args.get('datetime', datetime.now()),
            }
            sql = f"""
             INSERT INTO tariffs (user_id, language_code, name, tokens, amount, currency, status, created_at)
             VALUES
                 (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, tuple(data.values()))
                await connection.commit()
                return cursor.lastrowid

    async def get_payment_provider(self, args):
        """ Получает платёжные системы

        """
        sql, params = self.update_format("WHERE", args)
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM payment_providers {sql}"""
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()

    async def get_payment(self, args, order='DESC', start_limit=0, end_limit=100) -> list:
        """ Получает платёж/платежи

        """
        sql, params = self.update_format("WHERE", args, sep=" AND ")
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM payments {sql} ORDER BY id {order} LIMIT {start_limit}, {end_limit}"""
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()


    async def update_payment(self, payment_id: int, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE payments {sql} WHERE id = {payment_id}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def update_payment_provider(self, provider_id: int, args: dict = {}):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE payment_providers {sql} WHERE id = {provider_id}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def create_payment(self, args={}):
        async with await self.connect() as connection:
            data = {
                'from_user_id':        args.get('from_user_id', 0),
                'user_id':             args.get('user_id', 0),
                'tariff_id':           args.get('tarrif_id', 0),
                'payment_provider_id': args.get('payment_provider_id', 0),
                'amount':              args.get('amount', 0),
                'currency':            args.get('currency', 'rub'),
                'proxy_amount':        args.get('proxy_amount', 0),
                'xlink':               args.get('xlink', '-'),
                'label':               args.get('label', '-'),
                'payment_data':        json.dumps(args.get('payment_data', None)),
                'type':                args.get('type', 'tx'),
                'status':              args.get('status', 'new'),
                'close':               args.get('close', 0),
                'created_at':          args.get('datetime', datetime.now()),
            }
            sql = f"""
             INSERT INTO payments (from_user_id, user_id, tariff_id, payment_provider_id, amount, currency, proxy_amount, xlink, label, payment_data, type, status, close, created_at)
             VALUES
                 (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, tuple(data.values()))
                await connection.commit()
                return cursor.lastrowid

    async def get_promocode(self, args, start_limit=0, end_limit=40):
        """ Получает промокод

        """
        sql, params = self.update_format("WHERE", args, sep=" AND ")
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM promocodes {sql} LIMIT {start_limit}, {end_limit}"""
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()

    async def get_key(self, args={}):
        """ Получает ключ

        """
        sql, params = self.update_format("WHERE", args, sep=" AND ")
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""SELECT * FROM `keys` {sql}"""
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()

    async def create_key(self, args={}):
        async with await self.connect() as connection:
            data = {
                'user_id':             args.get('user_id', 0),
                'service':             args.get('service', 'openai'),
                'key':                 args.get('key', 0),
                'status':              args.get('status', 'active'),
                'reason':              args.get('reason', None),
                'created_at':          args.get('datetime', datetime.now()),
            }
            sql = f"""
             INSERT INTO `keys` (`user_id`, `service`, `key`, `status`, `reason`, `created_at`)
             VALUES
                 (%s, %s, %s, %s, %s, %s)
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, tuple(data.values()))
                await connection.commit()
                return cursor.lastrowid

    async def create_promocode(self, args={}):
        async with await self.connect() as connection:
            data = {
                'user_id':             args.get('user_id', 0),
                'code':                args.get('code', '-'),
                'usage':               args.get('usage', 0),
                'amount':              args.get('amount', 0),
                'status':              args.get('status', 'active'),
                'created_at':          args.get('datetime', datetime.now()),
            }
            sql = f"""
             INSERT INTO `promocodes` (`user_id`, `code`, `usage`, `amount`, `status`, `created_at`)
             VALUES
                 (%s, %s, %s, %s, %s, %s)
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, tuple(data.values()))
                await connection.commit()
                return cursor.lastrowid

    async def update_key(self, key: str, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE `keys` {sql} WHERE `key` = '{key}'
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def update_promocode(self, promocode_id: str, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE `promocodes` {sql} WHERE `id` = '{promocode_id}'
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def many_dialogs_update(self, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE `dialogs` {sql}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()

    async def delete_object(self, table, name_id, data):
        async with await self.connect() as connection:
            sql = f"""
             DELETE FROM `{table}` WHERE `{name_id}` = {data}
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql)
                await connection.commit()

    async def set_raw(self, rq):
        """ Выполняет сырой commit запрос

        """
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor) as cursor:
                sql = f"""{rq}"""
                await cursor.execute(sql)
                await connection.commit()

    async def get_raw(self, rq):
        """ Выполняет сырой fetch запрос

        """
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                sql = f"""{rq}"""
                await cursor.execute(sql)
                return await cursor.fetchall()

    async def call_procedure(self, proc):
        """ Выполняет процедуру

        """
        async with await self.connect() as connection:
            async with connection.cursor(SSCursor, DeserializationCursor, DictCursor) as cursor:
                    sql = f"""CALL {proc};"""
                    await cursor.execute(sql)
                    await connection.commit()

    async def mj_create_task(self, args={}):
        async with await self.connect() as connection:
            data = {
                'user_id':             args.get('user_id', 0),
                'task_id':             args.get('task_id', 0),
                'origin_task_id':      args.get('origin_task_id', 0),
                'task_type':           args.get('task_type', 'imagine'),
                'tokens':              args.get('tokens', 0),
                'status':              args.get('status', 'pending'),
                'prompt':              args.get('prompt', 'prompt'),
                'process_mode':        args.get('process_mode', 'fast'),
                'image_url':           args.get('image_url'),
                'images':              args.get('images'),
                'message_data':        json.dumps(args.get('message_data', {})),
                'data':                json.dumps(args.get('data', {})),
                'actions':             json.dumps(args.get('actions', {})),
                'created_at':          args.get('created_at', datetime.now()),
            }
            sql = f"""
             INSERT INTO `midjourney_tasks` (`user_id`, `task_id`, `origin_task_id`, `task_type`,  `tokens`, `status`, `prompt`, `process_mode`, `image_url`,  `images`, `message_data`, `data`, `actions`, `created_at`)
             VALUES
                 (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, tuple(data.values()))
                await connection.commit()
                return cursor.lastrowid

    async def mj_update_task(self, task_id: str, args: dict):
        sql, params = self.update_format("SET", args)
        async with await self.connect() as connection:
            sql = f"""
             UPDATE `midjourney_tasks` {sql} WHERE `task_id` = '{task_id}'
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, params)
                await connection.commit()


    async def create_subscribe(self, args={}):
        async with await self.connect() as connection:
            data = {
                'user_id':             args.get('user_id', 0),
                'provider_id':         args.get('provider_id', 0),
                'amount':              args.get('amount', 0),
                'tokens':              args.get('tokens', 0),
                'autopayment':         args.get('autopayment', 0),
                'tomorrow_notify':     args.get('tomorrow_notify', 0),
                'spent_nofity':        args.get('spent_nofity', 0),
                'status':              args.get('status', 'active'),
                'data':                json.dumps(args.get('data', {})),
                'expires_at':          args.get('expires_at', datetime.now()),
                'created_at':          args.get('created_at', datetime.now()),
            }
            sql = f"""
             INSERT INTO `subscriptions` (`user_id`, `provider_id`, `amount`, `tokens`, `autopayment`, `tomorrow_notify`, `spent_nofity`, `status`, `data`, `expires_at`, `created_at`)
             VALUES
                 (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            async with connection.cursor(SSCursor) as cursor:
                await cursor.execute(sql, tuple(data.values()))
                await connection.commit()
                return cursor.lastrowid
