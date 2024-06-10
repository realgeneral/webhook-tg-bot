# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from datetime import datetime
from loader import bot, cache, db, config, _

async def bot_username_in_cache():
    data = await bot.get_me()
    await cache.set('bot_username', data.username)

async def admin_parse_view_user(user):
    admin_get_user_keyboard = InlineKeyboardMarkup()
    admin_get_user_keyboard.add(InlineKeyboardButton(f"Подключить/продлить подписку", callback_data=f'admin.change_subscription_user_add_{user["telegram_id"]}'))
    user_subscribe = await db.get_subscription(user['id'])
    user_subscribe_active = user_subscribe['is_active'] if user_subscribe else user_subscribe
    user_subscribe_expires = None

    if user_subscribe:
        user_subscribe_expires = str(user_subscribe['expires_at'])
        admin_get_user_keyboard.add(InlineKeyboardButton(f"Отключить подписку", callback_data=f'admin.change_subscription_user_cancel_{user_subscribe["user_id"]}'))

    msg_user = _(
        'admin_get_user_text'
    ).format(
        user['telegram_id'],
        f"@{user['username']}",
        f"{bool(user_subscribe_active)} / {str(user_subscribe_expires)}",
        bool(user['is_admin']),
        user['created_at'],
        user['type'],
    )

    return msg_user, admin_get_user_keyboard


async def admin_handler_view_user(call):
    user = await db.get_chat_or_user(call.text)
    await bot.delete_message(call.chat.id, call.message_id-1)
    if user:
        msg_user, admin_get_user_keyboard = await admin_parse_view_user(user)
        await bot.send_message(
            call.from_user.id,
            msg_user,
            reply_markup=admin_get_user_keyboard,
        )
        return

    await bot.send_message(
        call.from_user.id,
        _('admin_get_user_not_found_text'),
        reply_markup=admin_cancel_action_keyboard
    )
    await bot.register_next_step_handler(call, admin_handler_view_user)
