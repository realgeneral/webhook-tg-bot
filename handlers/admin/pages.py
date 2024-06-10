# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, cache, db, root_dir, config as cfg, u, _
from states.states import EditPage
from keyboards.inline import BotKeyboard
from telebot.formatting import escape_markdown
from utils.strings import CallbackData
import json
import os
from pathlib import Path
from datetime import datetime

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data == CallbackData.admin_pages, role=['admin', 'demo'])
async def admin_pages_list(call):
    """ Отображает список страниц
    """
    pages = await db.get_pages()
    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=_('admin_page_home'),
        reply_markup=BotKeyboard.pages(u.get(), pages)
    )

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_view_page), role=['admin', 'demo'])
async def admin_preview_page(call):
    """ Отображает содержимое и кнопки управления страницей
    """
    page_id = call.data.replace(CallbackData.admin_view_page , '')
    page = await db.get_page({'id': page_id})

    if page['document'] == 'null':
        pass

    edit_page_text = _('admin_page_edit_home').format(page['page_title'])

    await bot.edit_message_text(
        chat_id    = call.message.chat.id,
        message_id = call.message.message_id,
        text       = page['page_content'],
        parse_mode = ''
    )
    await bot.send_message(
        chat_id=call.message.chat.id,
        text=edit_page_text,
        reply_markup=BotKeyboard.page_edit(u.get(), page),
    )

    # Для кнопки "Назад" из редактирования страницы
    await bot.delete_state(call.from_user.id)

@bot.callback_query_handler(is_chat=False, func=lambda call: call.data.startswith(CallbackData.admin_edit_page), role=['admin'])
async def admin_edit_page(call):
    """ Редактирование страницы
    """
    page_id = call.data.replace(CallbackData.admin_edit_page, "")
    page = await db.get_page({'id': page_id})

    await bot.set_state(call.from_user.id, EditPage.A1)

    async with bot.retrieve_data(call.from_user.id) as data:
        data['message_id'] = call.message.message_id
        data['page_id'] = page['id']

    edit_page_text = _('admin_page_edit_tmp')
    key_string_back_to = _('inline_back_to')

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=_('admin_page_edit_text').format(page['page_title']),
        reply_markup=BotKeyboard.smart({
            key_string_back_to: {'callback_data': CallbackData.admin_view_page+str(page['id'])}
        })
    )

@bot.message_handler(is_chat=False, state=EditPage.A1, role=['admin', 'demo'])
async def edit_page_text(message):
    async with bot.retrieve_data(message.from_user.id) as data:
        # Обрезаем лишние символы
        new_page_text = message.text[0:4000]
        new_page_text = new_page_text.replace('_', '\_')

        # Обновляем страницу
        await db.update_page(page_id=data['page_id'], args={'page_content': new_page_text})

        # Получаем актуальные данные и возвращаем в админку
        page = await db.get_page({'id': data['page_id']})
        edit_page_text = _('admin_page_edit_home').format(page['page_title'])

        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=data['message_id']
            )
        except Exception as e:
            pass

        await bot.send_message(
            chat_id=message.chat.id,
            text=_('admin_page_success_edit').format(page['page_title'])
        )
        await bot.send_message(
            chat_id    = message.chat.id,
            text       = page['page_content'],
            parse_mode = ""
        )
        await bot.send_message(
            chat_id=message.chat.id,
            text=edit_page_text,
            reply_markup=BotKeyboard.page_edit(u.get(), page)
        )

        await bot.delete_state(message.from_user.id)
