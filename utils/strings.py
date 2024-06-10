# Все права защищены. Публичное распространение кода запрещено.
# Почта: paschazverev@gmail.com
# Сайт: https://zverev.io
#
# © 2023, Павел Зверев

# Поздно спохватился, но перепишу под все запросы в следующих версиях
from telebot.callback_data import CallbackData, CallbackDataFilter

class CallbackData:
    """ Все строки для Callback Query

        Это может казаться неудобным, но спасает
        от переиспользования в разных файлах
    """
    admin = 'admin'

    # Главные разделы
    dialogs_chatgpt = 'bot.dialogs_chatgpt'
    create_dialog_chatgpt = 'bot.create_chatgpt_dialog'
    deactivate_chatgpt_dialog = 'bot.deactivate_chatgpt_dialog_'
    start_chatgpt_dialog = 'bot.start_chatgpt_dialog_'

    dalle = 'bot_dalle'
    dalle_variant = 'bot_dalle#variant_{0}'
    dalle_ratio = 'bot_dalle#ratio_{0}'

    midjourney = 'bot.midjourney'

    choose_language = 'choose_language_'
    user_subscribed = 'bot.is_subscription'

    # Stable
    stable_diffusion = 'bot_stable_diffusion'

    # Пользователь
    change_language = 'bot.change_language'
    refferal_program = 'bot.refferal_program'
    refferal_withdraw = 'bot.refferal_withdraw'
    profile = 'bot.profile'
    user_payments = 'bot.profile_payments'
    page = 'page#'
    user_home = 'bot.back'

    # Административная панель
    admin_home = 'admin.back_to_home'

    admin_bonuses = 'admin.bon'
    admin_bon_set_param = 'admin.bon_set_param|'

    admin_users = 'admin.users'
    admin_view_user = 'admin.view_user'
    admin_view_payment = 'admin.view_payment'
    admin_switch_user_param = 'admin.user_param|'
    admin_parse_user = 'admin.parse_user|'

    # OpenAi
    admin_home = 'admin.back_to_home'
    admin_unlimited_mode = 'admin.unlimited_mode'
    admin_openai = 'admin.openai'

    admin_chatgpt = 'admin.chatgpt'
    admin_chatgpt_set_param = 'admin.chatgpt_set_param|'
    admin_chatgpt_dialog_set = 'admin.chatgpt_dialog_set|'
    admin_chatgpt_keys = 'admin.chatgpt_keys'
    admin_chatgpt_dialogs = 'admin.chatgpt_dialogs'
    admin_chatgpt_dialog_view = 'admin.chatgpt_dialog_view_'
    admin_chatgpt_dialog_delete = 'admin.chatgpt_dialog_delete_'
    admin_chatgpt_create_dialog = 'admin.chatgpt_create_dialog'
    admin_chatgpt_create_dialog_lang = 'admin.chatgpt_create_dialog_lang'

    admin_recent_joined_users = 'admin.recent_joined_users'

    admin_dalle = 'admin.dalle'
    admin_dalle_set_param = 'admin.dalle_set_param|'

    admin_stable = 'admin.stable'
    admin_stable_set_param = 'admin.stable_set_param|'

    admin_midjourney = 'admin.mj'
    admin_mj_set_param = 'admin.mj_set_param|'

    admin_models = 'admin.models'
    admin_models_add = 'admin.models_add'

    admin_keys = 'admin.keys'
    admin_key_view = 'admin.key_view_'
    admin_key_create = 'admin.key_create'
    admin_key_set_param = 'admin.key_set_param|'
    admin_key_delete = 'admin.admin_key_delete|'
    admin_create_key_service = 'admin.create_key_service|'

    # Promocodes
    admin_promocodes = 'admin.promocodes'
    admin_promocode_view = 'admin.promocode_view_'
    admin_promocode_create = 'admin.promocode_create'
    admin_promocode_set_param = 'admin.promocode_set_param|'
    admin_promocode_delete = 'admin.admin_promocode_delete|'

    # Pages
    admin_pages = 'admin.pages'
    admin_edit_page = 'admin.pages.edit_'
    admin_view_page = 'admin.pages.preview_'

    # affiliate
    admin_affiliate = 'admin.affiliate'
    admin_affiliate_set_param = 'admin.affiliate_set_param|'

    admin_create_newsletter = 'admin.create_newsletter'

    # affiliate
    admin_channels = 'admin.channels'
    admin_channels_set_param = 'admin.channels_set_param|'
    admin_delete_channel = 'admin.channels_delete|'
    admin_create_channel = 'admin.channels_create'

    # shop
    admin_shop = 'admin.shop'
    admin_shop_tariffs = 'admin.shop_tariffs'
    admin_tariff = CallbackData('tariff_id', prefix='admin_tariff')
    admin_tariff_create = 'admin.shop_tariff_create'
    admin_tariff_archive = 'admin.tariff_archive'
    admin_tariff_set_param = 'admin.tariff_set_param|'
    admin_tc_cc = 'admin.tc_cc'
    admin_tariff_cr1 = 'admin.tariff_cr1'
    admin_tariff_crfinal = 'admin.tariff_crfinal'

    # providers
    admin_payment = 'admin.paymentId#'
    admin_accept_payment = 'admin.accept_pId#'
    admin_pay_txs = 'admin.pay_txs'
    admin_shop_providers = 'admin.shop_providers'
    admin_provider_set_param = 'admin.provider_set_param|'
    admin_provider = CallbackData('provider_id', prefix='admin_provider')

    admin_analytics = 'admin.analytics'
    admin_analytics_chapter = 'admin.analytics_chapter'
    admin_analytics_ref = 'admin.analytics_ref'

    # Магазин
    home_shop = 'bot#shop'
    shop_select_tariff = 'shop_select_tariff_'
    shop_select_provider = 'shop_select_provider_'

    promocode = 'activate_promocode'

    unlim_gpt35turbo = 'bot#unlim_gpt35turbo'
    unlim_gpt35turbo_check = 'bot#unlim_gpt35turbo_check'

    start_newsletter = 'admin.start_newsletter#'

    soon = 'bot.soon'

class CacheData:
    """ Все строки для Redis Cache

    """
    # UserId_dialog_DialogId
    dialog_save_history = "{0}_dialog_{1}"
    # UserId_dalle
    chatgpt_generation = "{0}_chatgpt"
    # UserId_dalle
    dalle_generation = "{0}_dalle"
    # UserId_stable
    stable_generation = "{0}_stable"
    # UserId_midjourney
    midjourney_generation = "{0}_midjourney"
    # last_use_bot_UserId
    last_use_bot = "last_use_bot_{0}"

    # keys:list
    keys_list = "keys:list"

    # keys:list
    stop_next_handler = "{0}_stop_next_handler"

    last_payment_mid = "{}_last_payment"
