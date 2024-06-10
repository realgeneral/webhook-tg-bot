from loader import bot, cache, db, config_path, config, _, u, loop
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from datetime import datetime, timedelta
from telebot.formatting import escape_markdown
from keyboards.inline import BotKeyboard
from states.states import BotState, AdminUsers
from utils.strings import CallbackData, CacheData
from utils.texts import Pluralize
from utils.configurable import config_update


admin_cancel_action_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton('Отменить действие', callback_data=CallbackData.admin_users)],
])

async def parse_admin_user():
    msg = _('admin_chapter_user').format(**{
        'tokens': config.get('default', 'free_tokens')
    })
    kb = BotKeyboard.smart({
        _('inline_search_user'): {'callback_data': CallbackData.admin_view_user},
        _('inline_admin_bonuses'): {'callback_data': CallbackData.admin_bonuses},
        # _('inline_recent_joined_users'): {'callback_data': CallbackData.admin_recent_joined_users},
        _('inline_welcome_bonus'): {'callback_data': 'admin.edit_welcome_bonus'},
        _('inline_back_to'): {'callback_data': CallbackData.admin_home},
    })

    return msg, kb

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == 'admin.edit_welcome_bonus', role=['admin', 'demo'])
async def callback_handler(call):
    """ Изменение приветственного бонуса
    """
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = _('input_new_value_param').format(_('welcome_bonus')),
        # reply_markup = kb
    )
    await bot.set_state(call.from_user.id, AdminUsers.B1)


@bot.message_handler(is_chat=False, state=AdminUsers.B1)
async def admin_add_tokens(message):
    """ Изменение параметров пользовательского раздела
    """
    tokens = 0

    try:
        tokens = int(message.text)
    except Exception as e:
        tokens = 0

    config.set('default', 'free_tokens', str(tokens))

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = _('param_value_updated').format(_('welcome_bonus')),
    )

    msg, kb = await parse_admin_user()
    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = msg,
        reply_markup = kb
    )

    await bot.delete_state(message.from_user.id)
    await config_update()

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_users, role=['admin', 'demo'])
async def callback_handler(call):
    """ Раздел пользователя
    """
    msg, kb = await parse_admin_user()
    await bot.edit_message_text(
        chat_id      = call.from_user.id,
        message_id   = call.message.message_id,
        text         = msg,
        reply_markup = kb
    )
    await bot.delete_state(call.from_user.id)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_view_user, role=['admin', 'demo'])
async def callback_handler(call):
    """ Настройки пользователя
    """
    await bot.edit_message_text(
        message_id=call.message.message_id,
        chat_id=call.message.chat.id,
        text=_('input_username_or_id'),
        reply_markup=admin_cancel_action_keyboard
    )

    await bot.set_state(call.from_user.id, BotState.search_user)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_switch_user_param), role=['admin'])
async def callback_handler(call):
    """ Переключение опций
    """
    guser = u.get()
    raw_params = call.data.replace(CallbackData.admin_switch_user_param, "").split('.')

    param = raw_params[0]
    user_id = raw_params[1]

    user = await db.get_user(user_id) or await db.get_user(user_id, type='chat')

    if param == 'switch_demo':
        switch_demo = {'user': 'demo', 'demo': 'user', 'admin': 'demo'}
        await db.update_user(
            user['telegram_id'],
            {'role': switch_demo.get(user['role'])}
        )
        user['role'] = switch_demo.get(user['role'])

    if param == 'switch_block':
        switch_block = {'user': 'blocked', 'blocked': 'user', 'admin': 'blocked'}
        await db.update_user(
            user['telegram_id'],
            {'role': switch_block.get(user['role'])}
        )
        user['role'] = switch_block.get(user['role'])

    if param == 'switch_unlim':
        switch_unlim = {0: 1, 1: 0}
        await db.update_user(
            user['telegram_id'],
            {'is_unlimited': switch_unlim.get(user['is_unlimited'])}
        )
        user['is_unlimited'] = switch_unlim.get(user['is_unlimited'])

    if param == 'switch_admin':
        admin_switcher = {'admin': 'user', 'user': 'admin'}

        if user_id.startswith("-"):
            await bot.answer_callback_query(
                call.id,
                _('admin_for_only_user'),
                show_alert=True
            )
            return

        if user['is_superuser'] == 1 or ['role'] == 'admin' and user['telegram_id'] == call.from_user.id:
            await bot.answer_callback_query(
                call.id,
                _('admin_cant_demote_himself'),
                show_alert=True
            )
            return

        await db.update_user(
            user['telegram_id'],
            {'role': admin_switcher.get(user['role'])}
        )

        user['role'] = admin_switcher.get(user['role'])

    if param == 'add_tokens':
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=_('input_amount_tokens').format(
                user['telegram_id'],
                user['username'] or _('neurouser'),
            ),
            parse_mode="HTML",
            reply_markup=BotKeyboard.smart({
                _('inline_back_to'): {'callback_data': CallbackData.admin_parse_user+str(user['telegram_id'])}
            })
        )

        await bot.set_state(call.from_user.id, AdminUsers.A1)

        async with bot.retrieve_data(call.from_user.id) as data:
            data['user_id'] = user_id

        return

    if param == 'zeroing':
        user['balance'] = 0
        await db.create_payment({
            'from_user_id':        guser['id'],
            'user_id':             user['id'],
            'type':                'zeroing',
            'label':               'admin',
            'status':              'success',
        })
        await bot.answer_callback_query(
            call.id,
            _('admin_user_zeroing_success'),
            show_alert=True
        )

    msg, kb = await admin_parse_view_user(user)
    await bot.edit_message_text(
        chat_id      = call.message.chat.id,
        message_id   = call.message.message_id,
        text         = msg,
        parse_mode   = "HTML",
        reply_markup = kb
    )


@bot.message_handler(is_chat=False, state=AdminUsers.A1)
async def admin_add_tokens(message):
    """ Зачисление токенов
    """
    admin = u.get()
    tokens = 0
    user_id = 0

    try:
        tokens = int(message.text)
    except Exception as e:
        tokens = 0

    async with bot.retrieve_data(message.from_user.id) as data:
        user_id = data['user_id']

    user = await db.get_user(data['user_id']) or await db.get_user(data['user_id'], type='chat')

    kb_admin = {
        _('inline_back_to'): {'callback_data': CallbackData.admin_parse_user+str(user['telegram_id'])}
    }
    numerals_tokens = _('numerals_tokens', user['language_code'])
    string_proxy_amount = Pluralize.declinate(tokens, numerals_tokens)

    if tokens <= 0:
        await bot.send_message(
            chat_id      = message.from_user.id,
            text         = _('error_add_tokens'),
            reply_markup = BotKeyboard.smart(kb_admin)
        )
        return

    await bot.send_message(
        chat_id      = message.from_user.id,
        text         = _('success_add_tokens'),
        reply_markup = BotKeyboard.smart(kb_admin)
    )

    await db.create_payment({
        'from_user_id':        admin['id'],
        'user_id':             user['id'],
        'proxy_amount':        tokens,
        'type':                'user',
        'label':               'admin',
        'status':              'success',
    })
    msg_user = _('success_tx_payment', user['language_code']).format(**{
        "tokens":     tokens,
        "p1":         string_proxy_amount.word,
        "id":         admin['telegram_id'],
        "username":   'admin',
    })
    kb_user = None
    if user['type'] == 'user':
        kb_user = BotKeyboard.smart({
            _('inline_back_to'): {'callback_data': CallbackData.user_home}
        })
    await bot.send_message(
        chat_id      = user['telegram_id'],
        text         = msg_user,
        reply_markup = kb_user
    )

    await bot.delete_state(message.from_user.id)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_parse_user), role=['admin'])
async def callback_handler(call):
    user_id = call.data.replace(CallbackData.admin_parse_user, '')
    user = await db.get_user(user_id) or await db.get_user(user_id, type='chat')

    msg, kb = await admin_parse_view_user(user)
    await bot.edit_message_text(
        message_id   = call.message.message_id,
        chat_id      = call.message.chat.id,
        text         = msg,
        parse_mode="HTML",
        reply_markup = kb
    )

    await bot.delete_state(call.from_user.id)

async def admin_parse_view_user(user):
    global_user = u.get()

    dict_user_role = _('dict_user_role')
    dict_user_type = _('dict_user_type')

    pm = CallbackData.admin_switch_user_param + "{0}." + str(user["telegram_id"])

    kb = InlineKeyboardMarkup(row_width=1)

    if user['type'] == 'user' and user['role'] in ['user', 'admin'] and user['is_superuser'] == 0:
        kb.add(
            InlineKeyboardButton(
                _('inline_set_admin') if user['role'] in ['user'] else _('inline_unset_admin'),
                callback_data=pm.format('switch_admin')
            ),
        )

    if user['type'] == 'user' and user['role'] in ['user', 'admin', 'blocked'] and user['is_superuser'] == 0:
        kb.add(
            InlineKeyboardButton(
                _('inline_unblock') if user['role'] in ['blocked'] else _('inline_block'),
                callback_data=pm.format('switch_block')
            )
        )

    if user['type'] == 'user' and user['role'] in ['user', 'demo'] and user['is_superuser'] == 0:
        kb.add(
            InlineKeyboardButton(
                _('inline_unset_demo') if user['role'] in ['demo'] else _('inline_set_demo'),
                callback_data=pm.format('switch_demo')
            )
         )

    kb.add(
        InlineKeyboardButton(
            _('inline_add_tokens'), callback_data=pm.format('add_tokens')
        ),
        InlineKeyboardButton(
            _('inline_zeriong_balance'), callback_data=pm.format('zeroing')
        ),
        InlineKeyboardButton(
            _('dict_switch_unlim').get(user['is_unlimited']), callback_data=pm.format('switch_unlim')
        ),
        InlineKeyboardButton(
            _('inline_back_to'), callback_data=CallbackData.admin_users
        )
    )

    last_use = await cache.get(
        CacheData.last_use_bot.format(user['telegram_id']),
    )

    msg = _('admin_get_user_text').format(**{
        'telegram_id':     user['telegram_id'],
        'username':        f"@{escape_markdown(user['username'] or _('neurouser'))}",
        'balance':          user['balance'],
        'role':             dict_user_role[user['role']],
        'created_at':       user['created_at'],
        'type':             dict_user_type[user['type']],
        'last_use':         last_use,
        'unlim':            _('dict_param_state').get(user['is_unlimited'])
    })

    return msg, kb


@bot.message_handler(is_chat=False, state=BotState.search_user)
async def admin_handler_view_user(message):
    """ Поиск юзера
    """
    username_or_id = message.text.replace('http://t.me/', '').replace('https://t.me/', '').replace('@', '')
    user = None

    try:
        user = await db.get_chat_or_user(username_or_id)
    except Exception as e:
        pass

    if user:
        msg_user, admin_get_user_keyboard = await admin_parse_view_user(user)
        await bot.send_message(
            message.from_user.id,
            msg_user,
            parse_mode="HTML",
            reply_markup=admin_get_user_keyboard,
        )
        await bot.delete_state(message.from_user.id)
        return

    await bot.send_message(
        message.from_user.id,
        _('admin_get_user_not_found_text'),
        reply_markup=admin_cancel_action_keyboard
    )
