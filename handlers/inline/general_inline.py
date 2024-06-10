# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from loader import bot, db, config, cache, _, loop
from utils.openai.chat_completion import chat_completion
from keyboards.inline import BotKeyboard
from utils.strings import CallbackData
from telebot.formatting import escape_markdown
from telebot import types
import asyncio
import re
from utils.balancing import BalancingKeys


# TODO: ДОПИСАТЬ таймеры для корректной обработки ошибок от answer_inline_query

prefix_ref = "#ref"

@bot.inline_handler(
    func=lambda query: query.query.startswith(prefix_ref)
)
async def empty_query(inline, data):
    """ Отправляет промо-текст реферальной программы

    """
    me = await bot.get_me()
    hint = _('inquery_refferal_promo').format(
        config['default']['free_tokens']
    )
    hint_inline_link = 'https://t.me/{0}?start=ref{1}'.format(
        me.username,
        inline.from_user.id
    )

    r = types.InlineQueryResultArticle(
            id='1',
            title=_('inquery_refferal_share'),
            input_message_content=types.InputTextMessageContent(
                message_text=hint,
                parse_mode="HTML"
            ),
            reply_markup=BotKeyboard.smart({
                _('inline_go_to_bot'): {"url": hint_inline_link}
            })
    )
    await bot.answer_inline_query(
        inline.id,
        [r],
        switch_pm_text=_('inquery_go_bot'),
        switch_pm_parameter='_',
        cache_time=90000
    )


@bot.inline_handler(
    func=lambda query: len(query.query) == 0 and
                       query.query.startswith(prefix_ref) is False
)
async def empty_query(inline, data):
    """ Запрос к CHATGPT через строку сообщений

        1. Отображает подсказки с информацией,
           что нужно делать
    """
    user = data['user']
    prompt = str(inline.query)

    hint = _('inquery_ask_chatgpt')

    if user is None:
        r = types.InlineQueryResultArticle(
                id='1',
                title=_('inquery_only_auth_user'),
                input_message_content=types.InputTextMessageContent(
                message_text=hint)
        )
        await bot.answer_inline_query(
            inline.id,
            [r],
            switch_pm_text=_('inquery_go_bot'),
            switch_pm_parameter='_',
            cache_time=0
        )
        return

    if user['balance'] <= 0:
        hint_send_answer = _('inquery_not_exist_tokens')
        openai_answer = _('inquery_not_exist_tokens')

        await bot.answer_inline_query(
            inline.id,
            [types.InlineQueryResultArticle(
                    id='1',
                    title=hint_send_answer,
                    input_message_content=types.InputTextMessageContent(
                        message_text=prompt + "\n\n" + openai_answer,
                    ),
            )],
            switch_pm_text=_('inquery_go_bot'),
            switch_pm_parameter='_',
            cache_time=0
        )

        return

    try:

        r = types.InlineQueryResultArticle(
                id='1',
                title=hint,
                input_message_content=types.InputTextMessageContent(
                message_text=_('inquery_ask_gpt_information'))
        )

        await bot.answer_inline_query(
            inline.id,
            [r],
            switch_pm_text=_('inquery_go_bot'),
            switch_pm_parameter='_',
            cache_time=0
        )
    except Exception as e:
        pass


@bot.inline_handler(
    func=lambda inline: len(inline.query) > 5 and
                (re.search(r'[!?]$', inline.query)
                or inline.query.endswith("-e")) == False and
                inline.query.startswith(prefix_ref) is False
)
async def empty_query(inline, data):
    """ Запрос к CHATGPT через строку сообщений

        2. Просит завершить предложение !, ?, -e
    """
    user = data['user']
    prompt = str(inline.query)

    if user is None:
        r = types.InlineQueryResultArticle(
                id='1',
                title=_('inquery_only_auth_user'),
                input_message_content=types.InputTextMessageContent(
                message_text=hint)
        )
        await bot.answer_inline_query(
            inline.id,
            [r1],
            switch_pm_text=_('inquery_go_bot'),
            switch_pm_parameter='_',
            cache_time=0
        )
        return

    if user is None:
        r = types.InlineQueryResultArticle(
                id='1',
                title=hint_end_message,
                input_message_content=types.InputTextMessageContent(
                message_text=hint)
        )
        await bot.answer_inline_query(
            inline.id,
            [r],
            cache_time=0
        )
        return

    hint = _('inquery_ask_chatgpt')
    hint_end_message = _('inquery_end_sentence')

    if user['balance'] <= 0:
        hint_send_answer = _('inquery_not_exist_tokens')
        openai_answer = _('inquery_not_exist_tokens')

        await bot.answer_inline_query(
            inline.id,
            [types.InlineQueryResultArticle(
                    id='1',
                    title=hint_send_answer,
                    input_message_content=types.InputTextMessageContent(
                        message_text=prompt + "\n\n" + openai_answer,
                    ),
            )],
            switch_pm_text=_('inquery_go_bot'),
            switch_pm_parameter='_',
            cache_time=0
        )

        return

    try:
        r = types.InlineQueryResultArticle(
                id='1',
                title=hint_end_message,
                input_message_content=types.InputTextMessageContent(
                message_text=hint)
        )

        if len(prompt) >= 254 and (re.search(r'[!?]$', inline.query) or inline.query.endswith("-e")) == False:
            r = types.InlineQueryResultArticle(
                    id='1',
                    title=_('inquery_end_sentence_big'),
                    input_message_content=types.InputTextMessageContent(
                    message_text=hint)
            )

        await bot.answer_inline_query(
            inline.id,
            [r],
            switch_pm_text=_('inquery_go_bot'),
            switch_pm_parameter='_',
            cache_time=0
        )
    except Exception as e:
        pass

@bot.inline_handler(
    func=lambda inline: len(inline.query) > 5 and
                        len(inline.query) < 255 and
                        (re.search(r'[.!?]$', inline.query) or inline.query.endswith("-e")) and
                        inline.query.startswith(prefix_ref) is False
)
async def empty_query(inline, data):
    """ Запрос к CHATGPT через строку сообщений

        3. Отправляет запрос к ChatGPT
    """
    user = data['user']
    hint_send_answer = _('inquery_mode_send_answer')
    openai_answer = _('inquery_answer_not_found')
    prompt = str(inline.query)

    if user is None:
        r = types.InlineQueryResultArticle(
                id='1',
                title=_('inquery_only_auth_user'),
                input_message_content=types.InputTextMessageContent(
                message_text=hint)
        )
        await bot.answer_inline_query(
            inline.id,
            [r],
            switch_pm_text=_('inquery_go_bot'),
            switch_pm_parameter='_',
            cache_time=0
        )
        return

    if user['balance'] <= 0:
        hint_send_answer = _('inquery_not_exist_tokens')
        openai_answer = _('inquery_not_exist_tokens')

        await bot.answer_inline_query(
            inline.id,
            [types.InlineQueryResultArticle(
                    id='1',
                    title=hint_send_answer,
                    input_message_content=types.InputTextMessageContent(
                    message_text=openai_answer)
            )],
            switch_pm_text=_('inquery_go_bot'),
            switch_pm_parameter='_',
            cache_time=0
        )

        return

    try:
        # Иницализируем класс распределения токенов
        balancer = BalancingKeys('openai', 50)

        # Берём ключ с наименьшим кол-вом соединений
        api_key = await balancer.get_available_key()
        completion, usage, errors = await chat_completion(
            api_key=api_key,
            model=config['openai']['model'],
            role=config['openai']['default_role'],
            prompt=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        openai_answer = completion
        if errors == []:
            await db.create_request(
                user['id'],
                0,
                'inline_chatgpt',
                escape_markdown(prompt),
                escape_markdown(completion),
                prompt_tokens=usage['prompt_tokens'],
                completion_tokens=usage['completion_tokens'],
                total_tokens=usage['total_tokens'],
                unlimited=int(config.getboolean('default', 'unlimited'))
            )
    except Exception as e:
        pass

    try:
        r1 = types.InlineQueryResultArticle(
                id='1',
                title=hint_send_answer,
                input_message_content=types.InputTextMessageContent(
                    message_text=prompt + "\n\n" + openai_answer,
                ),
        )
        await bot.answer_inline_query(inline.id, [r1], cache_time=0)
    except Exception as e:
        pass
        # try:
        #     await bot.send_message(
        #         user['telegram_id'],
        #         _('inquery_big_request').format(
        #             prompt,
        #             openai_answer,
        #         ),
        #         reply_markup=BotKeyboard.smart({
        #             _('inline_back_to_main_menu'): {"callback_data": CallbackData.user_home}
        #         })
        #     )
        # except Exception as e:
        #     pass
