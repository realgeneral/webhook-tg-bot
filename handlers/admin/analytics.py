# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config_path, config, _, u, loop
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from datetime import datetime, timedelta
from telebot.formatting import escape_markdown
from keyboards.inline import BotKeyboard
from utils.strings import CallbackData

async def admin_analytics_refferal(message):
    """ Главная страница анилитики рефералов
    """
    analytics = await db.get_raw("""
        SELECT u.reffer_id, MAX(u2.username) AS referrer_username, MAX(u2.telegram_id) AS referrer_telegram_id, w.balance, w.currency, COUNT(u.id) AS referrals_count
        FROM users u
        JOIN wallets w ON u.reffer_id = w.user_id
        LEFT JOIN users u2 ON u.reffer_id = u2.id
        WHERE w.type = 'refferal_cash'
        GROUP BY u.reffer_id, w.balance, w.currency
        ORDER BY referrals_count DESC
        LIMIT 0, 20;
    """)



    refferals = [f"{k['referrer_telegram_id']} (@{k['referrer_username']}) | {k['balance']} {k['currency']} | {k['referrals_count']}" for k in analytics]


    msg = _('admin_system_stats_refferals').format(**{
        'refferals': '\n'.join(refferals)
    })

    return msg, BotKeyboard.smart({
        _('inline_admin_analytics'): {'callback_data': CallbackData.admin_analytics},
        _('inline_admin_analytics_chapter'): {'callback_data': CallbackData.admin_analytics_chapter},
        _('inline_back_to'): {'callback_data': CallbackData.admin_home}
    }, row_width=1)

async def admin_analytics_chapter(message):
    """ Главная страница анилитики разделов
    """
    chapters_dict = _('dict_analytics_chapter')

    analytics = await db.get_raw("""
       SELECT
            section,
            COUNT(id) AS requests,
            COUNT(DISTINCT CASE WHEN DATE(created_at) = CURDATE() THEN id END) AS today
       FROM statistics GROUP BY section;
    """)

    chapters = [f"<b>{chapters_dict.get(k['section'], k['section'])}</b>: {k['requests'] or 0} (+{k['today'] or 0})" for k in analytics if not k['section'].startswith('source_')]

    sources = [f"<b>{k['section'].replace('source_', '')}</b>: {k['requests'] or 0} (+{k['today'] or 0})" for k in analytics if k['section'].startswith('source_')] or '-'

    msg = _('admin_system_stats_chapter').format(**{
        'chapters': '\n'.join(chapters),
        'sources': '\n'.join(sources),
        "username": await cache.get('bot_username'),
    })

    return msg, BotKeyboard.smart({
        _('inline_admin_analytics'): {'callback_data': CallbackData.admin_analytics},
        _('inline_admin_analytics_ref'): {'callback_data': CallbackData.admin_analytics_ref},
        _('inline_back_to'): {'callback_data': CallbackData.admin_home}
    }, row_width=1)


async def admin_analytics(message):
    """ Главная страница статистики
    """
    users = await db.get_raw("""
       SELECT
        COUNT(CASE WHEN type = 'user' AND is_active = 1 AND DATE(created_at) >= CURDATE() THEN 1 END) as today,
        COUNT(CASE WHEN type = 'user' AND is_active = 0 AND DATE(created_at) >= CURDATE() THEN 1 END) as users_blocked_count_today,
        COUNT(CASE WHEN type = 'user' AND MONTH(created_at) = MONTH(CURRENT_DATE()) THEN 1 END) as current_month_users,
        COUNT(CASE WHEN type = 'user' AND MONTH(created_at) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) THEN 1 END) as previous_month_users,
        COUNT(CASE WHEN type = 'user' AND is_active = 1 THEN 1 END) as `all`,
        COUNT(CASE WHEN role = 'admin' THEN 1 END) as `admins`,
        COUNT(CASE WHEN type = 'chat' AND DATE(created_at) >= CURDATE() THEN 1 END) as chats_today,
        COUNT(CASE WHEN type = 'chat' THEN 1 END) as chats,
        COUNT(CASE WHEN is_active = 0 THEN 1 END) as users_blocked_count
        FROM users;
    """)
    dialogs = await db.get_raw("""
       SELECT COUNT(*) as c FROM dialogs WHERE is_system = 0 AND DATE(created_at) >= CURDATE();
    """)

    request = await db.get_raw("""
       SELECT
        -- Кол-во активных пользователей СЕГОДНЯ
        COUNT(DISTINCT CASE WHEN DATE(created_at) = CURDATE() THEN user_id END) as active,

        -- Общее кол-во запросов к ChatGPT
        COUNT(DISTINCT CASE WHEN type = 'chatgpt' THEN id END) as chatgpt_count,
        -- Кол-во запросов к ChatGPT СЕГОДНЯ
        COUNT(DISTINCT CASE WHEN type = 'chatgpt' AND DATE(created_at) = CURDATE() THEN id END) as chatgpt_count_today,
        SUM(CASE WHEN type IN ('inline_chatgpt', 'chatgpt') AND MONTH(created_at) = MONTH(CURRENT_DATE()) THEN total_tokens ELSE 0 END) as chatgpt_count_current_month,
        SUM(CASE WHEN type IN ('inline_chatgpt', 'chatgpt') AND MONTH(created_at) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) THEN total_tokens ELSE 0 END) as chatgpt_count_previous_month,

        -- Общее кол-во запросов к ChatGPT через инлайн-режим
        SUM(CASE WHEN type = 'inline_chatgpt' THEN id ELSE 0 END) as inline_chatgpt_count,
        -- Общее кол-во запросов к ChatGPT через инлайн-режим СЕГОДНЯ
        SUM(CASE WHEN type = 'inline_chatgpt' AND DATE(created_at) = CURDATE() THEN id ELSE 0 END) as inline_chatgpt_count_today,

        -- Общее кол-во запросов к DALL-E
        COUNT(DISTINCT CASE WHEN type = 'dalle' THEN id END) as dalle_count,
        -- Общее кол-во запросов к DALL-E СЕГОДНЯ
        COUNT(DISTINCT CASE WHEN type = 'dalle' AND DATE(created_at) = CURDATE() THEN id END) as dalle_count_today,

        -- Общее кол-во запросов к Stable Diffusion
        COUNT(DISTINCT CASE WHEN type = 'stable_diffusion' THEN id END) as stable_count,
        -- Общее кол-во запросов к Stable Diffusion СЕГОДНЯ
        COUNT(DISTINCT CASE WHEN type = 'stable_diffusion' AND DATE(created_at) = CURDATE() THEN id END) as stable_count_today,

        -- Общее кол-во потраченных токенов за всё время к ChatGPT
        SUM(CASE WHEN type IN ('inline_chatgpt', 'chatgpt') THEN total_tokens ELSE 0 END) as total_spent_gpt,
        -- Общее кол-во потраченных токенов за всё время к ChatGPT за СЕГОДНЯ
        SUM(CASE WHEN type IN ('inline_chatgpt', 'chatgpt') AND DATE(created_at) = CURDATE() THEN total_tokens ELSE 0 END) as total_spent_gpt_today,

        -- Общее кол-во потраченных токенов за всё время к DALL-E
        SUM(CASE WHEN type IN ('dalle') THEN total_tokens ELSE 0 END) as total_spent_dalle,
        -- Общее кол-во потраченных токенов за всё время к DALL-E за СЕГОДНЯ
        SUM(CASE WHEN type IN ('dalle') AND DATE(created_at) = CURDATE() THEN total_tokens ELSE 0 END) as total_spent_dalle_today,
        SUM(CASE WHEN type IN ('dalle') AND MONTH(created_at) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) THEN total_tokens ELSE 0 END) as dalle_count_previous_month,
        SUM(CASE WHEN type IN ('dalle') AND MONTH(created_at) = MONTH(CURRENT_DATE()) THEN total_tokens ELSE 0 END) as dalle_count_current_month,

        -- Общее кол-во потраченных токенов за всё время к Stable Diffusion
        SUM(CASE WHEN type IN ('stable_diffusion') THEN total_tokens ELSE 0 END) as total_spent_stable,
        -- Общее кол-во потраченных токенов за всё время к Stable Diffusion за СЕГОДНЯ
        SUM(CASE WHEN type IN ('stable_diffusion') AND DATE(created_at) = CURDATE() THEN total_tokens ELSE 0 END) as total_spent_stable_today,

        SUM(CASE WHEN type IN ('stable_diffusion') AND MONTH(created_at) = MONTH(CURRENT_DATE - INTERVAL 1 MONTH) THEN total_tokens ELSE 0 END) as stable_count_previous_month,
        SUM(CASE WHEN type IN ('stable_diffusion') AND MONTH(created_at) = MONTH(CURRENT_DATE) THEN total_tokens ELSE 0 END) as stable_count_current_month
       FROM requests;
    """)
    shop_turnover = await db.get_raw("""
       SELECT
        currency,
        SUM(amount) AS total_amount
       FROM payments
       WHERE type = 'tx' AND status = 'success'
       GROUP BY currency;
    """)
    shop_summary = await db.get_raw("""
       SELECT
        SUM(CASE WHEN MONTH(created_at) = MONTH(CURRENT_DATE()) THEN amount ELSE 0 END) as payments_sum_current_month,
        SUM(CASE WHEN MONTH(created_at) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) THEN amount ELSE 0 END) as payments_sum_previous_month,
        SUM(CASE WHEN DATE(created_at) = CURRENT_DATE() THEN amount ELSE 0 END) as earn_today
       FROM payments
       WHERE
        type = 'tx' AND status = 'success'
    """)
    shop_proxy_amount = await db.get_raw("""
        SELECT
            SUM(CASE WHEN DATE(created_at) = CURDATE() THEN proxy_amount ELSE 0 END) AS tpx,
            SUM(proxy_amount) AS px,
            SUM(CASE WHEN MONTH(created_at) = MONTH(CURRENT_DATE()) THEN proxy_amount ELSE 0 END) as current_month_buy_tokens,
            SUM(CASE WHEN MONTH(created_at) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) THEN proxy_amount ELSE 0 END) as previous_month_buy_tokens
        FROM payments
        WHERE type = 'tx' AND status = 'success';
    """)
    shop_promocodes = await db.get_raw("""
        SELECT COUNT(*) AS c,
            COUNT(DISTINCT CASE WHEN DATE(created_at) = CURDATE() THEN user_id END) as ct,
            SUM(CASE WHEN MONTH(created_at) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) THEN 1 ELSE 0 END) as promocodes_count_previous_month,
            SUM(CASE WHEN MONTH(created_at) = MONTH(CURRENT_DATE()) THEN 1 ELSE 0 END) as promocodes_count_current_month
        FROM payments
        WHERE type = 'promocode' AND status = 'success';
    """)

    shop_promocodes_sum_tokens = await db.get_raw("""
        SELECT
            SUM(proxy_amount) AS c,
            SUM(CASE WHEN DATE(created_at) = CURDATE() THEN proxy_amount ELSE 0 END) AS ct,
            SUM(CASE WHEN MONTH(created_at) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH) THEN proxy_amount ELSE 0 END) AS promocodes_sum_previous_month,
            SUM(CASE WHEN MONTH(created_at) = MONTH(CURRENT_DATE()) THEN proxy_amount ELSE 0 END) AS promocodes_sum_current_month
        FROM payments
        WHERE type = 'promocode' AND status = 'success';
    """)

    currencies = _('dict_currency')
    shop_turnover = [f"{i['total_amount']} {currencies[i['currency']]}" for i in shop_turnover] or '-'

    dict_stat = {
        'users_blocked_count_today': users[0]['users_blocked_count_today'],
        'users_blocked_count': users[0]['users_blocked_count'],
        'users_count': users[0]['all'],
        'users_count_today': users[0]['today'],
        'previous_month_users': users[0]['previous_month_users'],
        'current_month_users': users[0]['current_month_users'],
        'admins_count': users[0]['admins'],
        'users_active_count': request[0]['active'],

        'chats_count': users[0]['chats'],
        'chats_count_today': users[0]['chats_today'],
        'chatgpt_count': request[0]['chatgpt_count'],
        'chatgpt_count_today': request[0]['chatgpt_count_today'],
        'chatgpt_count_current_month': request[0]['chatgpt_count_current_month'],
        'chatgpt_count_previous_month': request[0]['chatgpt_count_previous_month'],

        'chatgpt_inline_count': request[0]['inline_chatgpt_count'],
        'chatgpt_inline_count_today': request[0]['inline_chatgpt_count_today'],
        'chatgpt_dialogs_count': dialogs[0]['c'],
        'chatgpt_spent_tokens_count': request[0]['total_spent_gpt'] or 0,
        'chatgpt_spent_tokens_count_today': request[0]['total_spent_gpt_today'] or 0,

        'stable_spent_tokens_count': request[0]['total_spent_stable'] or 0,
        'stable_spent_tokens_count_today': request[0]['total_spent_stable_today'] or 0,
        'stable_count': request[0]['stable_count'],
        'stable_count_today': request[0]['stable_count_today'],
        'stable_count_current_month': request[0]['stable_count_current_month'] or 0,
        'stable_count_previous_month': request[0]['stable_count_previous_month'] or 0,

        'dalle_count': request[0]['dalle_count'] or 0,
        'dalle_count_today': request[0]['dalle_count_today'] or 0,
        'dalle_spent_tokens_count': request[0]['total_spent_dalle'] or 0,
        'dalle_spent_tokens_count_today': request[0]['total_spent_dalle_today'] or 0,
        'dalle_count_current_month': request[0]['dalle_count_current_month'] or 0,
        'dalle_count_previous_month': request[0]['dalle_count_previous_month'] or 0,

        'payments_sum': " / ".join(shop_turnover),
        'payments_sum_current_month': shop_summary[0]['payments_sum_current_month'] or 0,
        'payments_sum_previous_month': shop_summary[0]['payments_sum_previous_month'] or 0,
        'current_month_buy_tokens': shop_proxy_amount[0]['current_month_buy_tokens'] or 0,
        'previous_month_buy_tokens': shop_proxy_amount[0]['previous_month_buy_tokens'] or 0,
        'earn_today': shop_summary[0]['earn_today'] or 0,

        'promocodes_count_current_month': shop_promocodes[0]['promocodes_count_current_month'] or 0,
        'promocodes_count_previous_month': shop_promocodes[0]['promocodes_count_previous_month'] or 0,

        'promocodes_count': shop_promocodes[0]['c'] or 0,
        'promocodes_count_today': shop_promocodes[0]['ct'] or 0,
        'promocodes_tokens_sum': shop_promocodes_sum_tokens[0]['c'] or 0,
        'promocodes_tokens_sum_today': shop_promocodes_sum_tokens[0]['ct'] or 0,
        'payments_tokens_sum': shop_proxy_amount[0]['px'] or 0,
        'payments_tokens_sum_today': shop_proxy_amount[0]['tpx'] or 0,
        'promocodes_sum_current_month': shop_promocodes_sum_tokens[0]['promocodes_sum_current_month'] or 0,
        'promocodes_sum_previous_month': shop_promocodes_sum_tokens[0]['promocodes_sum_previous_month'] or 0,
    }

    try:
        mj_stat = await db.get_raw("""
            SELECT
                COUNT(*) AS total_requests,
                SUM(CASE WHEN DATE(created_at) = CURDATE() THEN 1 ELSE 0 END) AS requests_today,
                SUM(CASE WHEN MONTH(created_at) = MONTH(CURDATE()) THEN 1 ELSE 0 END) AS requests_this_month,
                SUM(CASE WHEN MONTH(created_at) = MONTH(CURDATE()) - 1 THEN 1 ELSE 0 END) AS requests_previous_month,
                SUM(tokens) AS total_tokens_spent,
                SUM(CASE WHEN DATE(created_at) = CURDATE() THEN tokens ELSE 0 END) AS tokens_spent_today,
                SUM(CASE WHEN MONTH(created_at) = MONTH(CURDATE()) - 1 THEN tokens ELSE 0 END) AS tokens_spent_previous_month,
                SUM(CASE WHEN MONTH(created_at) = MONTH(CURDATE()) THEN tokens ELSE 0 END) AS tokens_spent_this_month,
                AVG(process_time) AS average_process_time
            FROM midjourney_tasks;
        """)
        dict_stat.update({
            'mj_total_requests': mj_stat[0]['total_requests'],
            'mj_requests_today': mj_stat[0]['requests_today'],
            'mj_requests_this_month': mj_stat[0]['requests_this_month'],
            'mj_requests_previous_month': mj_stat[0]['requests_previous_month'],
            'mj_total_tokens_spent': mj_stat[0]['total_tokens_spent'],
            'mj_tokens_spent_today': mj_stat[0]['tokens_spent_today'],
            'mj_tokens_spent_previous_month': mj_stat[0]['tokens_spent_previous_month'],
            'mj_tokens_spent_this_month': mj_stat[0]['tokens_spent_this_month'],
            'mj_average_process_time': mj_stat[0]['average_process_time'],
        })
    except Exception as e:
        dict_stat.update({
            'mj_total_requests': 0,
            'mj_requests_today': 0,
            'mj_requests_this_month': 0,
            'mj_requests_previous_month': 0,
            'mj_total_tokens_spent': 0,
            'mj_tokens_spent_today': 0,
            'mj_tokens_spent_previous_month': 0,
            'mj_tokens_spent_this_month': 0,
            'mj_average_process_time': 0,
        })

    msg = _('admin_system_stats').format(**dict_stat)

    return msg, BotKeyboard.smart({
        _('inline_admin_analytics_chapter'): {'callback_data': CallbackData.admin_analytics_chapter},
        _('inline_admin_analytics_ref'): {'callback_data': CallbackData.admin_analytics_ref},
        _('inline_back_to'): {'callback_data': CallbackData.admin_home},
    })

@bot.callback_query_handler(role=['admin', 'demo'], func=lambda call: call.data == CallbackData.admin_analytics, is_chat=False)
async def callback_handler(call):
    """ Статистика бота по callback
    """
    await bot.delete_state(call.from_user.id)
    msg, kb = await admin_analytics(call)

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=msg,
        reply_markup=kb
    )

@bot.callback_query_handler(role=['admin', 'demo'], func=lambda call: call.data == CallbackData.admin_analytics_chapter, is_chat=False)
async def callback_handler(call):
    """ Статистика бота по callback
    """
    await bot.delete_state(call.from_user.id)
    msg, kb = await admin_analytics_chapter(call)

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=msg,
        reply_markup=kb,
        parse_mode='HTML'
    )

@bot.callback_query_handler(role=['admin', 'demo'], func=lambda call: call.data == CallbackData.admin_analytics_ref, is_chat=False)
async def callback_handler(call):
    """ Статистика бота по callback
    """
    await bot.delete_state(call.from_user.id)
    msg, kb = await admin_analytics_refferal(call)

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=msg,
        reply_markup=kb
    )
