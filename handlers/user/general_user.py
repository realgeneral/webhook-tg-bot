# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config as cfg, _, u
from utils.openai import chatgpt
from states.states import BotState, CreateDialog
from keyboards.inline import BotKeyboard
from datetime import datetime, timedelta
from utils.subscriptions import check_subscription
from utils.texts import Pluralize
from telebot.formatting import escape_markdown
from telebot.util import extract_arguments
from utils.strings import CallbackData, CacheData
from filters.main_filters import Statistics
from handlers.user.shop import calculate_tokens

from telebot.util import extract_arguments
from filters.main_filters import Statistics

import json

async def parse_home(first_name = None, user = None):
    """ Главная
    """
    user = user or u.get()
    parse_mode = 'Markdown'


    numerals_tokens = _('numerals_tokens')
    string_user_balance = Pluralize.declinate(user['balance'], numerals_tokens)

    home_page_db = await db.get_page({'slug': 'home'})


    start_text = home_page_db.get('page_content', None) or _('start_text', user['language_code'])

    


    if home_page_db.get('page_content', None):
        start_text = start_text.replace('\_', '_')
        parse_mode = 'HTML'

    # Изменяем default-язык
    # При следующем запросе язык будет подгружен
    msg = start_text.format(**{
        "first_name": escape_markdown(first_name) or _('neurouser'),
        "bot_username": escape_markdown(await cache.get('bot_username')),
        "free_tokens": cfg.getint('default', 'free_tokens'),
        "amount": user['balance'],
        "balance": string_user_balance.word
    })

    return msg, await BotKeyboard.home(user), parse_mode

async def parse_profile(user, first_name='-') -> tuple:
    """ Профиль пользователя

        :user: json
    """
    numerals_tokens = _('numerals_tokens')
    spent_tokens = await db.get_spent_tokens(user['id'])
    spent_tokens = int(spent_tokens.get('total_tokens'))

    string_balance = Pluralize.declinate(user['balance'], numerals_tokens)
    string_spent_balance = Pluralize.declinate(spent_tokens, numerals_tokens)

    stats = await db.get_raw(f"""
       SELECT
        SUM(CASE WHEN type IN ('chatgpt', 'inline_chatgpt') THEN total_tokens ELSE 0 END) as chatgpt_spent,
        SUM(CASE WHEN type IN ('dalle') THEN total_tokens ELSE 0 END) as dalle_spent,
        SUM(CASE WHEN type IN ('stable_diffusion') THEN total_tokens ELSE 0 END) as stable_spent
       FROM requests
       WHERE
        user_id = {user['id']};
    """)

    active_subscribe = await db.get_raw(f"""
        SELECT * FROM subscriptions WHERE status = 'active' AND user_id = {user['id']}
    """)

    msg = _('profile_text').format(**{
        "telegram_id":    user['telegram_id'],
        "balance":        user['balance'],
        "p1":             string_balance.word,
        "telegrma_name":  escape_markdown(first_name),
        "all_sum_tokens": spent_tokens,
        "p2":             string_spent_balance.word,
        'chatgpt_spent':  stats[0]['chatgpt_spent'] or 0,
        'dalle_spent':    stats[0]['dalle_spent'] or 0,
        'stable_spent':   stats[0]['stable_spent'] or 0,
        'data': calculate_tokens(user['balance'], lang_name='calculate_profile_tokens')
    })

    if active_subscribe:
        rem_tokens = await db.get_raw(f"""
           SELECT
               sum(total_tokens) as tokens
           FROM requests
           WHERE
               `user_id` = {user['id']} AND
               `unlimited` = 0 AND
               `is_sub` = 1 AND
               UNIX_TIMESTAMP(created_at) >= UNIX_TIMESTAMP('{active_subscribe[0]['created_at']}')
        """)

        rem_tokens = rem_tokens[0]['tokens'] or 0
        rem_tokens = int(active_subscribe[0]['tokens'] - rem_tokens)

        rem_tokens = 0 if rem_tokens < 0 else rem_tokens

        numerals_tokens = _('numerals_tokens')

        msg += '\n' + _('active_subscribe').format(**{
            'tokens': active_subscribe[0]['tokens'],
            't1': Pluralize.declinate(active_subscribe[0]['tokens'], numerals_tokens).word,
            'date': active_subscribe[0]['expires_at'].strftime(cfg.get('default', 'datetime_mask')),
            'rem': rem_tokens,
            't2': Pluralize.declinate(rem_tokens, numerals_tokens).word
        })

    return msg, BotKeyboard.profile()

async def string_parse_payment(payments) -> str:
    """ Формирует строку для отображения в разделе
        Мои платежи

        :payments: json
    """
    string_payments = _('payments')
    numerals_tokens = _('numerals_tokens')

    for payment in payments:
        payment_type = _('dict_payment_type')[payment['type']]
        payment.update({
            'currency': _('dict_currency')[payment['currency']],
            'amount':   int(payment['amount']),
            'label':    payment['label'].upper(),
        })

        string_proxy_amount = Pluralize.declinate(payment['proxy_amount'], numerals_tokens)

        string_payments += _('payment_string').format(**{
          'id':           payment['id'],
          'emoji_status': _('dict_emoji_payment_status')[payment['status']],
          'proxy_tokens': payment['proxy_amount'],
          'p1':           string_proxy_amount.word,
          'type':         payment_type.format(**payment,),
          'created_at':   payment['created_at'],
        })

    return string_payments

async def parse_page(user, slug) -> tuple:
    """ Возвращает данные о странице
        и её подстраницы с Inline клавиатурой

        :user: json
        :slug: str slug страницы
    """
    lang = user['language_code']

    page = await db.get_page({'slug': slug, 'language_code': lang})
    child_pages = await db.get_pages({
        'child_id': page['child_id'] or page['id'],
        'language_code': lang
    })

    string_back_to = _('inline_back_to_main_menu')
    string_contact_with_admin = _('inline_contact_with_admin')

    msg = (page.get(
        'page_content',
        _('page_not_found')
    ))

    kb = {}
    # Если есть привязанные страницы - добавляем
    for cpage in child_pages:
        cback = CallbackData.page + cpage['slug']

        if cpage['id'] == page['id']:
           cpage['page_title'] = "> " + cpage['page_title'] + " <"
           cback = "none"

        kb[cpage['page_title']] = {
            "callback_data": cback
        }

    kb[string_back_to] = {'callback_data': CallbackData.user_home}

    return msg, BotKeyboard.smart(kb)

async def parse_refferal_program():
    """ Парсит главную реф программы
    """
    user = u.get()
    text_wallets = ' ' # shitcode
    str_refferal_text = 'refferal_text'

    # Кол-во заработанных токенов (RAW запрос)
    earned_tokens = await db.get_raw(
        f"SELECT SUM(proxy_amount) AS tokens FROM payments WHERE `type` = 'refferal' AND `user_id` = {user['id']};"
    )

    if cfg.getboolean('default', 'affiliate_cash_mode'):
        str_refferal_text = 'refferal_text_cash'
        refferal_cash_wallets = await db.get_raw(
            f"SELECT * FROM wallets WHERE user_id = {user['id']} AND type = 'refferal_cash';"
        )
        if refferal_cash_wallets:
            currencies = _('dict_currency')
            wallets = [f"└ {str(w['balance'])} *{currencies.get(w['currency'], w['currency'])}*" for w in refferal_cash_wallets]
            text_wallets = _('refferal_cash_text').format(**{
                'wallets': "\n".join(wallets)
            })

    # Кол-во рефералов
    count_refferal = await db.get_count(
        table="users",
        q={"reffer_id": user['id']}
    ) or 0

    me = await cache.get('bot_username')

    refferal_home_text = _(str_refferal_text).format(
        cfg.get('default', 'affiliate_tokens'),
        cfg.get('default', 'affiliate_payment_percent'),
        count_refferal,
        earned_tokens[0]['tokens'] or 0,
        me,
        user['telegram_id'],
        text_wallets
    )

    return refferal_home_text, BotKeyboard.share_reffer_link(user, me)


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.choose_language))
async def handler_start_choose_language_callback(call, data):
    """ Выбор языка
    """
    user = data['user']
    language_code = call.data.replace(CallbackData.choose_language, '')
    user['language_code'] = language_code

    await db.update_user(
        call.message.chat.id,
        {"language_code": user['language_code']}
    )

    # Изменяем default-язык
    # При следующем запросе язык будет подгружен
    msg, kb, parse_mode = await parse_home(first_name=call.from_user.first_name)

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = parse_mode
    )


@bot.message_handler(is_chat=False, commands=['start'], stats='home', is_subscription=True)
async def start_handler(message, data):
    """ Главное меню  /start
    """
    user_id = message.from_user.id
    user = u.get()

    msg, kb, parse_mode = await parse_home(first_name=message.from_user.first_name)

    await bot.delete_state(message.from_user.id)
    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = parse_mode
    )


@bot.message_handler(is_chat=False, commands=['profile'], is_subscription=True, stats='profile')
async def profile(message, data):
    """ Профиль пользователя по команде /profile
    """
    user = data['user']

    msg, kb = await parse_profile(
        user,
        first_name=message.from_user.first_name
    )
    await bot.send_message(
        chat_id     = message.from_user.id,
        text        = msg,
        reply_markup=kb
    )

@bot.message_handler(is_chat=False, commands=['faq'], is_subscription=True)
async def faq(message, data):
    """ Показывает страницу Помощь
    """
    user = data['user']
    msg, kb = await parse_page(user, "faq")

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data in [CallbackData.unlim_gpt35turbo, CallbackData.unlim_gpt35turbo_check])
async def unlim_gpt35turbo(call, data):
    """ Безлимит на >= GPT-3.5
    """
    msg = _('unlim_gpt35turbo')

    unlim = await check_subscription(u.get(), {'from_user_id': call.from_user.id}, False)
    msg += '\n\n' + _('dict_unlim_gpt35turbo').get(unlim, False)

    if call.data == CallbackData.unlim_gpt35turbo_check and not unlim:
        await bot.answer_callback_query(
            call.id,
            _('warning_subscribe_for_unlum'),
            show_alert = True
        )


    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        parse_mode   = "Markdown",
        reply_markup = await BotKeyboard.subscribe_channel(
            back_button      = True,
            button_subscribe = 'inline_unlim_enabled' if unlim else 'inline_subscribe_check',
            callback_data    = CallbackData.unlim_gpt35turbo_check,
        )
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.page))
async def page(call, data):
    """ Отображает страницу
    """
    user = data['user']
    slug = call.data.replace(CallbackData.page, '')
    msg, kb = await parse_page(user, slug)

    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.user_home, stats='home')
async def home_callback(call, data):
    """ Главная страница
    """
    await bot.delete_state(call.from_user.id)

    msg, kb, parse_mode = await parse_home(first_name=call.from_user.first_name)

    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = parse_mode,
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.soon)
async def soon(call, data):
    """ soon
    """
    await bot.answer_callback_query(
        call.id,
        _('coming_soon'),
        show_alert=True
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.user_subscribed)
async def subscribe_handler(call, data):
    """ Обработчик кнопки подписки на канал
    """
    user = u.get()
    numerals_tokens = _('numerals_tokens')
    string_user_balance = Pluralize.declinate(user['balance'], numerals_tokens)

    if cfg.getboolean('subscribe', 'required_subscribe'):
        is_subscribed = await check_subscription(
            u.get(),
            {'from_user_id': call.from_user.id},
            False
        )

        if is_subscribed == False:
            await bot.answer_callback_query (
                call.id,
                text       = _('warning_subscribe'),
                show_alert = True
            )
            return

        # Обновляет статус пользователя
        await db.update_user(call.from_user.id, {"is_active": is_subscribed})

    msg, kb, parse_mode = await parse_home(first_name=call.from_user.first_name)

    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = parse_mode,
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.user_payments)
async def user_pyaments(call, data):
    user = u.get()

    payments = await db.get_payment({'user_id': user['id']}, end_limit=5)

    # Если платежей нет, высвечивем всплывашку
    if payments == []:
        await bot.answer_callback_query(
            call.id,
            _('payments_not_found'),
            show_alert=True
        )
        return

    msg = await string_parse_payment(payments)

    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = BotKeyboard.smart({
            _('inline_back_to'): {"callback_data": CallbackData.profile}
        })
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.profile, stats='profile')
async def callback_profile(call, data):
    """ Пользователь
    """
    msg, kb = await parse_profile(u.get(), call.message.chat.first_name)
    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.change_language)
async def choose_lang(call, data):
    """ Выбор языка
    """
    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = _('choose_language'),
        parse_mode   = "Markdown",
        reply_markup = BotKeyboard.choose_language()
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.refferal_program, stats='refferal_program')
async def refferal_callback(call, data):
    """ Рефералка
    """
    msg, kb = await parse_refferal_program()
    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = 'HTML'
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.refferal_withdraw, stats='refferal_withdraw')
async def withdrawal_ref_amount(call, data):
    """ Вывод денег из рефералки
    """
    # user = u.get()
    # currencies = _('dict_currency')
    #
    # wallets = await db.get_raw(f"""
    #     SELECT * FROM wallets WHERE `type` = 'refferal_cash' AND user_id = {user['id']}
    # """)

    # if not wallets:
    await bot.answer_callback_query(
        call.id,
        _('wallets_not_found'),
        show_alert=True
    )
    return
    #
    # await bot.edit_message_text(
    #     chat_id      = call.message.chat.id,
    #     message_id   = call.message.message_id,
    #     text         = msg,
    #     reply_markup = kb
    # )

@bot.message_handler(is_chat=False, commands=['ref'], stats='refferal_program', is_subscription=True)
async def ref_command(message, data):
    """ Показывает страницу реф программы
    """
    msg, kb = await parse_refferal_program()

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb,
        parse_mode   = 'HTML'
    )
