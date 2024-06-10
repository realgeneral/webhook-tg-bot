# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telebot.util import quick_markup
from languages.language import lang_variants
from loader import bot, db, config, _, cache, u
from utils.strings import CallbackData
from utils.functions import openai_chatgpt_models

import json
import re

class BotKeyboard:
    """ Клавиатуры

        Основа: quick_markup.
        В некоторых ситуациях используются types.*
    """
    @staticmethod
    async def home(user):
        """ Клавиатура /start
        """
        if not user:
            return None

        kb = InlineKeyboardMarkup(row_width=1)
        system_dialog = await db.get_dialog({'is_system': 1, 'language_code': user['language_code']}, end_limit=1)

        if system_dialog:
            did = system_dialog[0]['id']
            kb.row(
                InlineKeyboardButton(
                    _('inline_start_chat_gpt', user['language_code']),
                    callback_data=CallbackData.start_chatgpt_dialog+str(did)
                ),
                InlineKeyboardButton(
                    _('inline_chat_gpt', user['language_code']),
                    callback_data=CallbackData.dialogs_chatgpt
                )
            )

        # kb.row(
        #     InlineKeyboardButton(
        #         _('inline_dalle', user['language_code']),
        #         callback_data=CallbackData.dalle
        #     ),
        #     InlineKeyboardButton(
        #         _('inline_stable_diffusion', user['language_code']),
        #         callback_data=CallbackData.stable_diffusion
        #     ),
        # )


        kb.row(
            InlineKeyboardButton(
                _('inline_midjourney', user['language_code']),
                callback_data=CallbackData.midjourney
            ),
            InlineKeyboardButton(
                _('inline_dalle', user['language_code']),
                callback_data=CallbackData.dalle
            ),
        )

        kb.row(
            InlineKeyboardButton(
                _('inline_stable_diffusion', user['language_code']),
                callback_data=CallbackData.stable_diffusion
            ),
            InlineKeyboardButton(
                _('inline_whisper', user['language_code']),
                callback_data=CallbackData.soon
            ),
        )

        kb.row(
            InlineKeyboardButton(
                _('inline_profile', user['language_code']),
                callback_data=CallbackData.profile
            ),
            InlineKeyboardButton(
                _('inline_buy_subscribe', user['language_code']),
                callback_data=CallbackData.home_shop
            ),
        )

        kb.row(
            InlineKeyboardButton(
                _('inline_refferal_program_short', user['language_code']),
                callback_data=CallbackData.refferal_program
            ),
            InlineKeyboardButton(
                _('inline_support', user['language_code']),
                callback_data=CallbackData.page+'faq'
            ),
        )

        if config.getboolean('subscribe', 'unlim_gpt35turbo'):
            # Добавляем кнопку админки на главной
            kb.add(InlineKeyboardButton(
                _('inline_unlim_gpt', user['language_code']),
                callback_data=CallbackData.unlim_gpt35turbo
            ))

        if user.get('role', 'user') in ['admin', 'demo']:
            # Добавляем кнопку админки на главной
            kb.add(InlineKeyboardButton(
                _('inline_admin_panel', user['language_code']),
                callback_data=CallbackData.admin_home
            ))

        return kb

    @staticmethod
    async def start_gpt_dialog(user):
        """ Клавиатура /start
        """
        kb = InlineKeyboardMarkup(row_width=1)
        system_dialog = await db.get_dialog({'is_system': 1, 'language_code': user['language_code']}, end_limit=1)

        if system_dialog:
            did = system_dialog[0]['id']
            kb.row(
                InlineKeyboardButton(
                    _('inline_start_chat_gpt', user['language_code']),
                    callback_data=CallbackData.start_chatgpt_dialog+str(did)
                ),
                InlineKeyboardButton(
                    _('inline_chat_gpt', user['language_code']),
                    callback_data=CallbackData.dialogs_chatgpt
                )
            )

        return kb

    # ненужный дубликат, переделать
    @staticmethod
    async def subscribe_channel(
        lang             = config['default']['language'],
        callback_data    = CallbackData.user_subscribed,
        button_subscribe = 'inline_subscribe_channel_success',
        back_button      = False
    ):
        """ Отображение ссылок на каналы
            и кнопки "Я подписался"
        """
        kb = {}
        tg_url = config.get('default', 'telegram_url')
        channels = config['subscribe']['channels'].split("\n")

        # Перебираю каналы из конфига
        for n, channel in enumerate(channels):
            try:
                channel = channel.split("|")
                rkey = f"{channel[0]}_sub_channel"
                username = await cache.get(rkey)
                username = json.loads(username) if username else None
                if not username:
                    d = await bot.get_chat(channel[0])
                    await cache.set(
                        rkey,
                        json.dumps({
                            # 'username': d.username,
                            'name': d.title,
                        })
                    )
                    await cache.expire(rkey, 300)
                    username = json.loads(await cache.get(rkey))
                # name = _('inline_subscribe_channel', lang).format((n+1))
                # name = tg_url + username if username else channel[1]
                kb[username['name']] = {'url': channel[1]}
            except Exception as e:
                print(e)
                continue

        kb.update({
            _(button_subscribe, lang): {'callback_data': callback_data}
        })

        if back_button:
            kb.update({
                _('inline_back_to', lang): {'callback_data': CallbackData.user_home}
            })

        return quick_markup(kb, row_width=1)

    @staticmethod
    def choose_language():
        """ Выбор языка

            Перебирает доступные языковые коды
            и добавляет их в клавиатуру.
        """
        langs = lang_variants.copy()
        kb = {}

        for code in langs:
            kb.update({
                _('name', code=code): {'callback_data': CallbackData.choose_language+code}
            })

        return quick_markup(kb)

    @staticmethod
    def payment_providers(payment_providers):
        """ Платёжные шлюзы
        """
        langs = lang_variants.copy()
        str_back_to = _('inline_back_to')

        kb = {}
        for p in payment_providers:
            kb[p['name']] = {
                "callback_data": CallbackData.shop_select_provider + str(p['id'])
            }

        kb[str_back_to] = { "callback_data": CallbackData.home_shop }

        return quick_markup(kb, row_width=1)

    @staticmethod
    def back_to_main_menu():
        """ Возвращает в главное меню
        """
        kb = {
            _('inline_back_to_main_menu'): {"callback_data": CallbackData.user_home}
        }

        return quick_markup(kb, row_width=1)

    @staticmethod
    def profile():
        """ Меню профиля
        """
        kb = {
            _('inline_change_language'): {"callback_data": CallbackData.change_language},
            _('inline_payments'): {"callback_data": CallbackData.user_payments}
        }

        kb.update({
            _('inline_back_to_main_menu'): {"callback_data": CallbackData.user_home}
        })

        return quick_markup(kb, row_width=1)

    @staticmethod
    def create_inline_keyboard(buttons_list, row_width):
        keyboard = InlineKeyboardMarkup(row_width=row_width)
        num_buttons = len(buttons_list)
        buttons_list = buttons_list.copy()

        # Проверка на нечетность количества кнопок
        if num_buttons % 2 != 0:
            buttons_list.append(None)
            num_buttons += 1

        for i in range(0, num_buttons, row_width):
            row_buttons = buttons_list[i:i+row_width]

            if row_buttons[-1] is None:
                del row_buttons[-1]

            keyboard.row(*row_buttons)

        return keyboard

    @staticmethod
    def dalle_configuration(variant='1:1'):
        """ Конфигуратор DALL-E
        """
        kb = {}
        ratios = {
            '1:1': '1024x1024',
            '9:16': '1024x1792',
            '16:9': '1792x1024',
        }

        for i in ratios.keys():
            checked = "✅ " if variant == i else ''
            kb.update({
                _('inline_dalle_ratio').format(checked, i): {'callback_data': CallbackData.dalle_ratio.format(i)}
            })

        kb.update({
            _('inline_back_to_main_menu'): {'callback_data': CallbackData.user_home}
        })

        return quick_markup(kb, 3)

    @staticmethod
    def back_to_main_menu_dalle():
        """ Меню DALL-E после генерации
        """
        kb = {
            _('inline_dalle_generate'): {"callback_data": CallbackData.dalle},
            _('inline_back_to_main_menu'): {"callback_data": CallbackData.user_home}
        }

        return quick_markup(kb, row_width=1)

    @staticmethod
    async def newsletter(link: list = []):
        """ Создание рассылки
        """
        links = await cache.get("newsletter_data_links")
        links = json.loads(links) if links else []

        result_markup = InlineKeyboardMarkup()

        if len(links) < 5:
            result_markup.add(
                InlineKeyboardButton('Добавить ссылку', callback_data='admin.send_newsletter_add_link')
            )

        if links:
            for k, v in enumerate(links):
                lnk = InlineKeyboardButton(v.get('name'), url=v.get('link'))
                lnk.url = v.get('link')
                if v.get('link').startswith('_'):
                    lnk.url = None
                    lnk.callback_data = v.get('link')[1:]
                result_markup.row(
                    lnk,
                    # InlineKeyboardButton(
                    #     '❌',
                    #     callback_data=f'admin.delete_newsletter_link|{k}'
                    # ),
                )

        result_markup.add(
            InlineKeyboardButton(_('who_send_newsletter'), callback_data=f'{CallbackData.start_newsletter}#all')
        )

        dict_type = _('dict_type_user_newsletter')
        result_markup.add(
            InlineKeyboardButton(dict_type.get('all'), callback_data=f'{CallbackData.start_newsletter}all')
        )
        result_markup.add(
            InlineKeyboardButton(dict_type.get('free'), callback_data=f'{CallbackData.start_newsletter}free')
        )
        result_markup.add(
            InlineKeyboardButton(dict_type.get('sub'), callback_data=f'{CallbackData.start_newsletter}sub')
        )

        result_markup.add(
            InlineKeyboardButton("🗑 Отменить", callback_data='admin.back_to_home')
        )

        return result_markup

    @staticmethod
    def gpt_dialog():
        """ Клавиатура в ChatGPT
        """
        kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        kb.row(
            KeyboardButton(_('reply_dialog_clear')),
            KeyboardButton(_('reply_end_dialog'))
        )

        return kb

    @staticmethod
    def gpt_models():
        """ Модели
        """
        kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)

        models = list(openai_chatgpt_models().keys())
        for m in models:
            kb.add(
                KeyboardButton(m),
            )

        return kb

    @staticmethod
    def remove_reply():
        """ Удаляет ReplyKeyboardMarkup клавиатуру
        """
        return ReplyKeyboardRemove(selective=False)

    @staticmethod
    def back_to_create_dialog_chatgpt():
        """ Назад к диалогам в ChatGPT
        """
        return quick_markup({
            _('inline_back_to_dialogs_chatgpt'): {"callback_data": CallbackData.dialogs_chatgpt}
        }, row_width=1)

    @staticmethod
    def share_reffer_link(user, me):
        """ Меню в реферальной программе
        """
        kb = {}

        if config.getboolean('default', 'affiliate_cash_mode'):
            kb.update({
                _('inline_withdraw'): {"callback_data":  CallbackData.refferal_withdraw}
            })

        kb.update({
            _('inline_refferal_share_text'): {"switch_inline_query":  _('refferal_promo_share_text').format(me, user['telegram_id'])},
            _('inline_back_to'): {"callback_data":  CallbackData.user_home}
        })
        return quick_markup(kb, row_width=1)

    @staticmethod
    def next_new_dialog(dialog_id):
        """ Перейти в новый диалог
        """
        kb = {
            _('inline_start_dialog'): {
                "callback_data": CallbackData.start_chatgpt_dialog+str(dialog_id)
            },
            _('inline_back_to_dialogs_chatgpt'): {
                "callback_data": CallbackData.dialogs_chatgpt
            },
        }

        return quick_markup(kb, row_width=1)

    @staticmethod
    async def create_dialog_chatgpt(user):
        """ Клавиатура диалогов / создания диалога
        """
        dialogs = await db.get_dialogs(user['id'])
        system_dialogs = await db.get_system_dialogs(
            lang_code=user['language_code']
        )

        kb = InlineKeyboardMarkup(row_width=2)
        system_kbs = []

        if system_dialogs is not None:
            for dialog in system_dialogs:
                system_kbs.append(
                    InlineKeyboardButton(
                        dialog['title'],
                        callback_data=f'bot.start_chatgpt_dialog_{dialog["id"]}'
                    )
                )

            if len(system_kbs) > 0:
                kb = BotKeyboard.create_inline_keyboard(system_kbs, 2)

        if dialogs:
            kbs = []
            for dialog in dialogs:
                kb.add(
                    InlineKeyboardButton(
                        dialog['title'],
                        callback_data=f'bot.start_chatgpt_dialog_{dialog["id"]}'
                    ),
                    InlineKeyboardButton(
                        _('inline_delete_dialog'),
                        callback_data=f'bot.deactivate_chatgpt_dialog_{dialog["id"]}'
                    )
                )

        kb.add(
            InlineKeyboardButton(
                _("inline_create_dialog"),
                callback_data='bot.create_chatgpt_dialog'
            )
        )

        kb.add(
            InlineKeyboardButton(
                _("inline_back_to_main_menu"),
                callback_data=CallbackData.user_home
            )
        )

        return kb

    @staticmethod
    def pages(user, pages):
        """ Страницы
        """
        lang = user['language_code']
        kb = {}

        for page in pages:
            title = page['page_title'] + f" {_('icon', page['language_code'])}"
            data = CallbackData.admin_view_page+str(page['id'])

            kb.update({
                title: {"callback_data": data}
            })

        kb.update({
            _('inline_back_to'): {"callback_data": CallbackData.admin_home}
        })

        return quick_markup(kb, row_width=2)

    @staticmethod
    def page_edit(user, page):
        """ Страницы
        """
        lang = user['language_code']
        kb = InlineKeyboardMarkup()

        kb.add(
            InlineKeyboardButton(
                _('inline_admin_edit_page'),
                callback_data=CallbackData.admin_edit_page+str(page['id'])
            )
        )

        kb.add(
            InlineKeyboardButton(
                _('inline_back_to'),
                callback_data=CallbackData.admin_pages
            ),
        )

        return kb

    @staticmethod
    def smart(json, row_width=1):
        """ Кастомная клавиатура из JSON

            :json: клавиатура
            :row_width: сетка
        """

        return quick_markup(json, row_width=row_width)
