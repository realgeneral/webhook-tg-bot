# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, config as cfg, _
from states.states import Shop
from keyboards.inline import BotKeyboard
from datetime import datetime, timedelta
from utils.texts import Pluralize
from telebot import types
from telebot.formatting import escape_markdown
from utils.strings import CallbackData, CacheData
from utils.payment_providers import payment_drivers
import json

def get_tariff_name(tariff: json):
    name:            str = ''
    str_currency:    str = _('dict_currency')
    amount = str(round(tariff['amount'], 2)).rstrip("0").rstrip(".")

    if tariff['days_before_burn'] > 0:
        name = _('tariff_sub_name').format(
            tariff['tokens'],
            tariff['days_before_burn'],
            Pluralize.declinate(tariff['days_before_burn'], _('numerals_days'), type=3).word,
            amount,
            str_currency.get(tariff['currency'])
        )

    if tariff['days_before_burn'] == 0:
        name = _('tariff_name').format(
            tariff['name'],
            amount,
            str_currency.get(tariff['currency'])
        )

    return name

def calculate_tokens(tokens, lang_name = 'calculate_tokens'):
    """ Считает на что хватит токенов
    """
    #
    # полностью переделать, буэ
    #
    numerals_requests = _('numerals_requests')

    gpt3 = int(tokens / 1000)

    gpt4 = int(tokens / 5000)
    gpt4 = 1 if gpt4 < 1 else gpt4

    dalle = int(tokens / cfg.getint('openai', 'dalle_request_tokens'))

    stabletext = int(tokens / cfg.getint('stable_diffusion', 'tti_price'))
    stableimage = int(tokens / cfg.getint('stable_diffusion', 'iti_price'))

    mjtti = int(tokens / cfg.getint('midjourney', 'tti_price'))

    return _(lang_name).format(**{
        'gpt3': gpt3,
        'gpt3p': Pluralize.declinate(gpt3, numerals_requests).word,
        'gpt4': gpt4,
        'gpt4p': Pluralize.declinate(gpt4, numerals_requests).word,
        'dalle': dalle,
        'dallep': Pluralize.declinate(dalle, numerals_requests).word,
        'stabletext': stabletext,
        'stabletextp': Pluralize.declinate(stabletext, numerals_requests).word,
        'stableimage': stableimage,
        'stableimagep': Pluralize.declinate(stableimage, numerals_requests).word,
        'mj': mjtti,
        'mjp': Pluralize.declinate(mjtti, numerals_requests).word,
    })

async def home_shop(user, sub = True) -> tuple:
    """ Возвращает текст/клавиатуру
        главной страницы магазина токенов
    """
    tsql = "SELECT * FROM tariffs WHERE status = 'active'"
    if sub: tsql += 'AND days_before_burn > 0'
    if not sub: tsql += 'AND days_before_burn = 0'

    tariffs = await db.get_raw(tsql)

    str_back_to:     str = _('inline_back_to')
    str_promocode:   str = _('inline_promocode')
    str_currency:    str = _('dict_currency')
    str_tariff_name: str = _('tariff_name')

    buttons = {}
    for t in tariffs:
        name = get_tariff_name(t)
        buttons[name] = {
            "callback_data": CallbackData.shop_select_tariff + str(t['id'])
        }

    if sub: buttons[_('inline_buy_tokens')] = { "callback_data": CallbackData.home_shop+'_tokens' }

    if not sub: buttons[_('inline_buy_subscribe')] = { "callback_data": CallbackData.home_shop }

    buttons[str_promocode] = { "callback_data": CallbackData.promocode }
    buttons[str_back_to] = { "callback_data": CallbackData.user_home }

    return _('shop_sub_home') if sub else _('shop_home'), BotKeyboard.smart(buttons)

@bot.message_handler(is_chat=False, commands=['shop'], stats='shop', is_subscription=True)
async def message_handler_shop_home(message, data):
    """ Главная страница магазина по команде
    """
    msg, kb = await home_shop(user=data['user'])
    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb
    )
    await bot.delete_state(message.from_user.id)
    await bot.set_state(message.from_user.id, Shop.payment)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.home_shop), is_subscription=True, stats='shop')
async def callback_handler_shop_home(call, data):
    """ Главная страница магазина по callback_query
    """
    sub = False if call.data.endswith('tokens') else True
    msg, kb = await home_shop(user=data['user'], sub=sub)

    try:
        await bot.edit_message_text(
            chat_id      = call.from_user.id,
            message_id   = call.message.message_id,
            text         = msg,
            reply_markup = kb
        )
    except Exception as e:
        await bot.send_message(
            chat_id      = call.from_user.id,
            text         = msg,
            reply_markup = kb
        )

    await bot.set_state(call.from_user.id, Shop.payment)

@bot.message_handler(is_chat=False, commands=['promocode'], stats='activate_promocode', is_subscription=True)
async def callback_handler_shop_home(message, data):
    """ Страница активации промокода по команде
    """
    str_back_to = _('inline_back_to')

    kb = {}
    kb[str_back_to] = { "callback_data": CallbackData.user_home }

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = _('promocode'),
        reply_markup = BotKeyboard.smart(kb)
    )
    await bot.set_state(message.from_user.id, Shop.promocode)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.promocode, is_subscription=True, stats='activate_promocode')
async def callback_handler_shop_home(call, data):
    """ Страница активации промокода
    """
    str_back_to = _('inline_back_to')

    kb = {}
    kb[str_back_to] = { "callback_data": CallbackData.home_shop }

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('promocode'),
        reply_markup = BotKeyboard.smart(kb)
    )
    await bot.set_state(call.from_user.id, Shop.promocode)

@bot.message_handler(is_chat=False, state=Shop.promocode, is_subscription=True)
async def message_handler_shop_home(message, data):
    """ Активация промокода
    """
    user = data['user']
    promocode = message.text

    str_back_to = _('inline_back_to')
    str_back_to = _('inline_back_to')

    msg = _('promocode_inactive')
    numerals_tokens = _('numerals_tokens')

    kb = {}
    kb[str_back_to] = { "callback_data": CallbackData.home_shop }

    promocode_exist = await db.get_promocode({
        'code': promocode,
        'status': 'active',
    })

    promocode_was_used = await db.get_payment({
        'user_id': user['id'],
        'label': str(promocode),
        'type': 'promocode',
    })

    if promocode_exist != [] and promocode_was_used == []:
        await db.call_procedure(
            f"activate_promocode({user['id']}, '{str(promocode)}')"
        )

        await bot.delete_state(message.from_user.id)

        promocode_tokens = promocode_exist[0].get('amount')
        msg = _('promocode_activated').format(**{
            "amount_tokens": promocode_tokens,
            "p1": Pluralize.declinate(promocode_tokens, numerals_tokens).word
        })

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = BotKeyboard.smart(kb)
    )


@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.shop_select_tariff), state=Shop.payment, is_subscription=True, stats='select_tariff')
async def callback_handler_select_provider(call, data):
    """ Выбор платёжного шлюза
    """
    tariff_id = call.data.replace(CallbackData.shop_select_tariff, '')

    payment_providers = await db.get_payment_provider({'status': 'active'})
    msg = _('shop_select_provider')

    async with bot.retrieve_data(call.from_user.id) as data:
        data['tariff_id'] = tariff_id
        tariff = await db.get_tariff({'id': tariff_id})

        msg += _('shop_select_tariff').format(**{
            'name': get_tariff_name(tariff[0])
        })
        try:
            msg += calculate_tokens(tariff[0]['tokens'])
        except Exception as e:
            print(e)


    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = BotKeyboard.payment_providers(payment_providers)
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.shop_select_provider), state=Shop.payment, is_subscription=True)
async def callback_handler_payment(call, data):
    """ Страница оплаты

        #
        #
        # Полностью переписать под классы / разделить логику на компоненты
        #
        #
    """
    user = data['user']

    str_back_to:    str = _('inline_back_to')
    str_currency:   str = _('dict_currency')
    str_pay:        str = _('inline_pay')
    str_payment_id: str = "#{0}"

    provider_id = call.data.replace(CallbackData.shop_select_provider, '')
    payment_date = datetime.now().strftime(cfg.get('default', 'datetime_mask'))

    payment_id = 0
    extra_info = None

    tariff = {}
    async with bot.retrieve_data(call.from_user.id) as data:
        tariff = await db.get_tariff({'id': data['tariff_id']})

    buttons = {}
    xlink = None

    payment_provider = await db.get_payment_provider({'id': provider_id})
    slug_provider = payment_provider[0].get('slug')

    if payment_provider[0].get('slug') == 'self':
        extra_info = _('extra_info_self_payment')

    if payment_provider[0].get('status') == 'inactive':
        await bot.answer_callback_query(
            call.id,
            _('payment_provider_error'),
            show_alert=True
        )
        return

    payment_label = cfg.get('default', 'payment_label').format(**{
        'tariff_id': tariff[0].get('id'),
        'user_id':   user['id'],
        'datetime':  payment_date
    }).replace(" ", "")

    # Проверяем, создавался ли уже похожий платёж
    # Если платёж находится в статусе pending, то показываем его юзеру
    # Как правило система отменит платежи, у которых время на оплату истекло
    payment_exist = await db.get_payment({
        'user_id': user.get('id'),
        'payment_provider_id': payment_provider[0].get('id'),
        'tariff_id': tariff[0].get('id'),
        'status': 'pending',
    })

    if payment_exist:
        payment_date = payment_exist[0].get('created_at').strftime(
            cfg.get('default', 'datetime_mask')
        )
        payment_id = payment_exist[0].get('id')
        payment_link = payment_exist[0].get('xlink')
        buttons[str_pay] = { "url": payment_link } if payment_provider[0].get('webapp_popup') == 0 else { "web_app": types.WebAppInfo(payment_link) }

        xlink = payment_exist[0].get('xlink')

    if not payment_exist and payment_drivers.get(slug_provider):
        payment_id = await db.create_payment({
            'user_id':             user['id'],
            'tarrif_id':           tariff[0].get('id'),
            'currency':            tariff[0].get('currency'),
            'payment_provider_id': payment_provider[0].get('id'),
            'amount':              tariff[0].get('amount'),
            'proxy_amount':        tariff[0].get('tokens'),
            'label':               payment_label,
            'xlink':               '-',
            'payment_data':        "sub" if tariff[0].get('days_before_burn') > 0 else None,
            'status':              'pending',
        })

        provider = payment_drivers[slug_provider](
            api_token=payment_provider[0].get('payment_token'),
            amount=int(tariff[0].get('amount')),
            label=str(payment_label),
            tariff=tariff[0],
            provider=payment_provider[0]
        )

        payment_form = await provider.create_payment_link(payment_id)
        xlink = payment_form['link_for_customer']

        pay_args = {'xlink': xlink}

        if payment_form is None:
            await bot.answer_callback_query(
                call.id,
                _('payment_provider_error'),
                show_alert=True
            )
            return

        if payment_form.get('label'):
            payment_label = payment_form.get('label')
            pay_args.update({'label':  payment_form.get('label')})
        if payment_form.get('extra_info_string_key'):
            extra_info = _(payment_form.get('extra_info_string_key'))

        buttons[str_pay] = { "url": xlink } if payment_provider[0].get('webapp_popup') == 0 else { "web_app": types.WebAppInfo(xlink) }

        await db.update_payment(
            payment_id = payment_id,
            args = pay_args
        )


    buttons[str_back_to] = { "callback_data": CallbackData.home_shop }

    msg = _('shop_payment_receipt').format(**{
        "payment_id":    payment_id,
        "tariff_name":   get_tariff_name(tariff[0]),
        "amount":        tariff[0].get('amount'),
        "currency":      str_currency[tariff[0].get('currency')],
        "provider_name": payment_provider[0].get('name'),
        "date":          payment_date,
        "payment_time":  int(payment_provider[0].get('payment_time')),
        "xlink":         xlink,
        "extra_info":   extra_info or ''
    })

    await cache.set(
        CacheData.last_payment_mid.format(call.from_user.id),
        call.message.message_id
    )

    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = BotKeyboard.smart(buttons)
    )
