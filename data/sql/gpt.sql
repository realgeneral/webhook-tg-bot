# ************************************************************
# Sequel Pro SQL dump
# Version 5446
#
# https://www.sequelpro.com/
# https://github.com/sequelpro/sequelpro
#
# Host: 127.0.0.1 (MySQL 8.0.23)
# Database: gdegaz
# Generation Time: 2024-01-24 13:41:12 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
SET NAMES utf8mb4;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table dialogs
# ------------------------------------------------------------

DROP TABLE IF EXISTS `dialogs`;

CREATE TABLE `dialogs` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL DEFAULT '0',
  `language_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'ru',
  `title` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `role` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `model` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'gpt-3.5-turbo-0613',
  `max_tokens` int NOT NULL DEFAULT '0',
  `temperature` float NOT NULL DEFAULT '0',
  `top_p` float NOT NULL DEFAULT '0',
  `presence_penalty` float NOT NULL DEFAULT '0',
  `frequency_penalty` float NOT NULL DEFAULT '0',
  `animation_text` tinyint(1) NOT NULL DEFAULT '0',
  `count_history_messages` int NOT NULL DEFAULT '3' COMMENT 'Важно понимать, что 1 - это 2. В одной строке находится question/answer.',
  `is_system` tinyint(1) NOT NULL DEFAULT '0',
  `is_active` int NOT NULL DEFAULT '1',
  `created_at` timestamp NOT NULL,
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=169 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `dialogs` WRITE;
/*!40000 ALTER TABLE `dialogs` DISABLE KEYS */;

INSERT INTO `dialogs` (`id`, `user_id`, `language_code`, `title`, `role`, `model`, `max_tokens`, `temperature`, `top_p`, `presence_penalty`, `frequency_penalty`, `animation_text`, `count_history_messages`, `is_system`, `is_active`, `created_at`, `updated_at`)
VALUES
	(1,1,'ru','💬 Общение','ChatGPT','gpt-3.5-turbo-16k-0613',4050,0.5,1,0.5,0.5,1,1,1,1,'2023-06-23 08:00:35','2024-01-10 15:54:05'),
	(2,1,'ru','💻 Программист','1. Ты профессиональный Middle+ программист;\n2. Отвечай профессиональными ответами;\n3. Работай только в контексте своей области.','gpt-3.5-turbo',4050,0.3,1,0.1,0.1,0,1,1,1,'2023-06-23 08:00:35','2023-11-06 12:38:47'),
	(3,1,'ru','⚖️ Юрист','1. Ты профессиональный юрист по кодексам и праву в Российской Федерации;\n2. Оказывай помощь по юридическим вопросам;\n3. Работай только в контексте своей области.','gpt-3.5-turbo',4050,0.3,1,0.3,0.3,0,2,1,1,'2023-06-23 08:00:35','2023-11-06 12:38:47'),
	(4,1,'ru','🌏 Переводчик','1. Ты профессиональный переводчик;\n2. Переводи любой поступающий текст на указанный язык, если язык не указан переводи на английский;\n3. Работай только в контексте своей области.','gpt-3.5-turbo',4050,0.3,1,0.3,0.3,0,1,1,1,'2023-06-23 08:00:35','2023-11-06 12:38:47');

/*!40000 ALTER TABLE `dialogs` ENABLE KEYS */;
UNLOCK TABLES;

# Dump of table midjourney_tasks
# ------------------------------------------------------------

DROP TABLE IF EXISTS `midjourney_tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `midjourney_tasks` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL DEFAULT '0',
  `task_id` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '0',
  `origin_task_id` varchar(256) DEFAULT NULL,
  `task_type` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'imagine',
  `tokens` int DEFAULT '0',
  `status` set('pending','staged','processing','finished','failed','retry') NOT NULL DEFAULT 'processing',
  `prompt` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `process_mode` set('relax','fast','turbo') NOT NULL DEFAULT 'relax',
  `model_version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `image_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `file_id` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `doc_file_id` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `data` json DEFAULT NULL,
  `actions` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `message_data` json DEFAULT NULL,
  `process_time` int DEFAULT NULL,
  `error_messages` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `images` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `image_urls` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `retry_count` int DEFAULT NULL,
  `sended` int NOT NULL DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


# Dump of table keys
# ------------------------------------------------------------

DROP TABLE IF EXISTS `keys`;

CREATE TABLE `keys` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL DEFAULT '0',
  `service` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'openai',
  `key` varchar(512) NOT NULL DEFAULT '',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active',
  `reason` varchar(512) DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



# Dump of table pages
# ------------------------------------------------------------

DROP TABLE IF EXISTS `pages`;

CREATE TABLE `pages` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `child_id` int NOT NULL DEFAULT '0',
  `language_code` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'ru',
  `slug` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `page_title` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `page_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `document` json DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `pages` WRITE;
/*!40000 ALTER TABLE `pages` DISABLE KEYS */;

INSERT INTO `pages` (`id`, `user_id`, `child_id`, `language_code`, `slug`, `page_title`, `page_content`, `document`, `updated_at`, `created_at`)
VALUES
	(1,1,0,'ru','faq','Помощь','❔Выберите интересующий вас раздел\n\n',NULL,'2023-07-31 11:27:50','2023-07-19 20:27:41'),
	(2,1,1,'ru','tokens','🔹 Токены','*🔹 Что такое токен?*\n\nТокен — это валюта нашего бота. С помощью неё вы можете общаться с ChatGPT, генерировать изображения через DALL-E и MidJourney.\n\n*🔹 Как тратятся токены в ChatGPT?*\n— 1 токен ≈ 1 символ на русском\n— 1 токен ≈ 4 символам на английском\n\n*🔹 Как они тратятся в DALL-E?*\n— 1000 токенов = 1 изображение\n\n*🔹 У меня не осталось токенов, что делать?*\n— Вы можете купить токены в разделе «💎 Магазин». /shop\n— Вы можете следить за постами в наших каналах, находить в постах промокоды и активировать их в разделе  «💎 Магазин»  по кнопке «🔢 Активировать промокод» и пользоваться ботом бесплатно. Попробуйте найти их по хештегу #PROMO. Промокоды многоразовые и вы точно сможете их активировать.\n\n❗️ Во всех разделах бот уведомляет вас о том, сколько токенов было затрачено и/или будет затрачено и сколько токенов осталось.',NULL,'2023-08-08 11:16:02','2023-07-19 20:27:41');

INSERT INTO `pages` (`id`, `user_id`, `child_id`, `language_code`, `slug`, `page_title`, `page_content`, `document`, `updated_at`, `created_at`)
VALUES
	(3,1,1,'ru','payments','💎 Платежи','*Оплата тарифов*\n\nВсе наши тарифы представлены в разделе «💎 Магазин». /shop\n\n⌛ Токены зачисляются на ваш баланс автоматически в течении 5 минут после оплаты.\n\n❗️ В случае если вы оплатили, но токены не зачислились в течении 5 минут, напишите администратору по кнопке ниже.\n\n*Статусы платежей:*\n🆕 — новый, ожидает проверки;\n⏳ — ожидает платёж и проверяет оплату;\n🟢 — платёж завершен;\n🔴 — платёж отклонён или истекло время ожидания.\n\n*Типы платежей:*\n*1. Оплата ...* — оплата тарифа или услуги;\n*2. Промокод ...* — был активирован промокод;\n*3. Реферальная программа* — начисление токенов за нового реферала или за оплату тарифа;\n*4. Обнуление баланса* — происходит в случае мошенничества или блокировки аккаунта за неоднократное нарушение правил сервиса.',NULL,'2023-08-08 10:21:18','2023-07-19 20:27:41'),
	(4,1,1,'ru','roles','💬  ChatGPT','*💬 ChatGPT*. Ответы на часто задаваемые вопросы.\n\n*— У меня было 50 токенов на балансе, но мой запрос всё равно обработался и забрал больше, почему?*\nНе волнуйтесь, это нормально. Мы даём право на последний бесплатный запрос. Это значит, что если запрос к чату затратил больше токенов, чем у вас есть, то бот спишет только те, что у вас остались и не будет уводить ваш баланс токенов в минус.\n\n*— Что за параметр «Включить/выключить показ затрат» в диалоге с ChatGPT?*\nВ включенном состоянии этот параметр  отправляет вам информацию о стоимости каждого запроса, сделанного Вами в рамках диалога или вызова функции /gpt _ваш запрос_.\n\n*— Почему чат сохраняет не всю историю, а только последние несколько сообщений?*\nСистема хранит только последние 6 сообщений в чате Это сделано для экономии токенов и избежания ошибок со стороны OpenAi. _Помните, диалог с сохранением истории тратит намного больше токенов, чем без сохранения._',NULL,'2023-08-08 10:50:28','2023-07-19 20:27:41');

INSERT INTO `pages` (`id`, `user_id`, `child_id`, `language_code`, `slug`, `page_title`, `page_content`, `document`, `updated_at`, `created_at`)
VALUES
	(5,1,1,'ru','ads','💵 Сотрудничество','*📣 Реклама и сотрудничество*\n\nПо рекламе/сотрудничеству и предложениям по улучшению бота пишите по контактам ниже.\n\nПавел — https://t.me/paulfake',NULL,'2023-08-08 11:14:42','2023-07-19 20:27:41'),
	(12,1,0,'en','faq','Help','❔Choose\n\n',NULL,'2023-08-02 10:38:34','2023-07-19 20:27:41'),
	(13,1,12,'en','tokens','🔹 Tokens','Tokens',NULL,'2023-08-02 11:07:01','2023-07-19 20:27:41'),
	(14,1,12,'en','payments','💎 Payments','Tarrifs',NULL,'2023-08-08 10:12:27','2023-07-19 20:27:41'),
	(15,1,12,'en','roles','💬  ChatGPT','*💬 ChatGPT*. Ответы на часто задаваемые вопросы.\n\n*— У меня было 50 токенов на балансе, но мой запрос всё равно обработался и забрал больше, почему?*\nНе волнуйтесь, это нормально. Мы даём право на последний бесплатный запрос. Это значит, что если запрос к чату затратил больше токенов, чем у вас есть, то бот спишет только те, что у вас остались и не будет уводить ваш баланс токенов в минус.\n\n*— Что за параметр «Включить/выключить показ затрат» в диалоге с ChatGPT?*\nВ включенном состоянии этот параметр  отправляет вам информацию о стоимости каждого запроса, сделанного Вами в рамках диалога или вызова функции /gpt _ваш запрос_.\n\n*— Почему чат сохраняет не всю историю, а только последние несколько сообщений?*\nСистема хранит только последние 6 сообщений в чате Это сделано для экономии токенов и избежания ошибок со стороны OpenAi. _Помните, диалог с сохранением истории тратит намного больше токенов, чем без сохранения._',NULL,'2023-08-08 10:50:24','2023-07-19 20:27:41');

INSERT INTO `pages` (`id`, `user_id`, `child_id`, `language_code`, `slug`, `page_title`, `page_content`, `document`, `updated_at`, `created_at`)
VALUES
	(16,1,12,'en','ads','💵 Ads','Рекламочкка',NULL,'2023-08-02 11:07:04','2023-07-19 20:27:41'),
	(17,1,1,'ru','data','📖 Политика хранения данных','*📖 Политика хранения данных*\n\nМы трепетно относимся к данным наших пользователей и поэтому решили написать эту политику, чтобы вы были уведомлены, как мы храним данные. \n\nАдмиинстрация бота имеет доступ только к управлению вашим аккаунтом (блокировка, выдача определённых прав и иные сервисные функции), но прав на доступ к истории ваших запросов у неё нет.\n\nНиже приведён перечь данных, которые мы временно храним на своих серверах.\n\n*ChatGPT*\n1. История ваших запросов в диалоге хранится на сервере до момента, пока вы не выполните очистку диалога по команде «/clear» или «Очистить историю».\n2. История ваших запросов через команду «/gpt _вопрос_» или «@PremiumAiBot _запрос_» хранится до конца суток и автоматически очищается системой.\n\n*DALL-E*\nИстория ваших запросов  хранится до конца суток и автоматически очищается системой. Система хранит информацию запрос-ссылки (на сервере OpenAi). \n\n❗️*Система очищает только вопрос-ответ и хранит информацию о потраченных токенах за запрос для извлечения статистики по тратам.*',NULL,'2023-08-22 10:22:49','2023-07-19 20:27:41');

INSERT INTO `pages` (`id`, `user_id`, `child_id`, `language_code`, `slug`, `page_title`, `page_content`, `document`, `updated_at`, `created_at`)
VALUES
	(18,1,12,'en','data','📖 Data storage policy','*📖 Data storage policy*\n\nWe care about our users\' data, so we decided to write this policy so that you can be informed about how we store data. \n\nThe bot administration only has access to your account management (blocking, granting certain rights and other service functions), but they do not have access to your request history.\n\nBelow is a list of data that we temporarily store on our servers.\n\n*ChatGPT*\n1. The history of your requests in the dialog is stored on the server until you clear the dialog using the command \"/clear\" or \"Clear history\".\n2. The history of your requests via the command \"/gpt question\" or \"@PremiumAiBot request\" is stored until the end of the day and is automatically cleared by the system.\n\n*DALL-E.*\nYour query history is stored until the end of the day and is automatically cleared by the system. The system stores the query-reference information (on the OpenAi server). \n\n❗️System clears only the query-reply and stores information about the tokens spent per query to extract statistics on spending.',NULL,'2023-08-22 10:24:58','2023-07-19 20:27:41');

INSERT INTO `pages` (`id`, `user_id`, `child_id`, `language_code`, `slug`, `page_title`, `page_content`, `document`, `updated_at`, `created_at`)
VALUES
	(19,1,1,'ru','policy_chargeback','Политика возвратов','Возвраты',NULL,'2023-08-08 11:14:42','2023-07-19 20:27:41'),
	(20,1,1,'ru','offer','Оферта','Оферта',NULL,'2024-01-11 12:43:51','2023-07-19 20:27:41'),
	(21,1,1,'ru','terms','Пользовательское соглашение','Пользовательское соглашение',NULL,'2024-01-11 12:43:51','2023-07-19 20:27:41');

/*!40000 ALTER TABLE `pages` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table payment_providers
# ------------------------------------------------------------

DROP TABLE IF EXISTS `payment_providers`;

CREATE TABLE `payment_providers` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `language_code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'ru',
  `name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '',
  `description` varchar(112) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '',
  `currency` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '',
  `currencies` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'RUB',
  `slug` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'driver',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active',
  `autopayments` tinyint NOT NULL DEFAULT '0',
  `payment_time` float NOT NULL DEFAULT '30',
  `payment_token` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '',
  `data` varchar(512) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL,
  `updated_at` timestamp NOT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `payment_providers` WRITE;
/*!40000 ALTER TABLE `payment_providers` DISABLE KEYS */;

INSERT INTO `payment_providers` (`id`, `language_code`, `name`, `description`, `currency`, `currencies`, `slug`, `status`, `autopayments`, `payment_time`, `payment_token`, `data`, `created_at`, `updated_at`)
VALUES
	(1,'ru','ЮMoney/Банковская карта','Юмани (прямой перевод)','руб.','RUB','yoomoney','inactive',0,30,'4100116758227010.58279B039D66761AF41A99D1594C4B3F1A2E31B0EC1B91F847B06F282BEF142590B0958A21EB14116AC169523DC7C640B435CC3FF95AAA17DA76BB8FA052613C5EEBFE6D3640B49608C63B8D1B7A44305D613F8C0F669596673457A1A70FE25C37D031DDAF5A8CA826B1F4876E240A2CBF988E0BB31FFB8F667E87A831C1516D','0','2023-07-23 15:05:49','2024-01-24 16:39:32'),
	(2,'ru','ЮКасса','ЮКасса (для самозанятых, ИП, ООО)','руб.','RUB','yookassa','inactive',1,30,'test_gz_Prm2GBfa-QFTNy8KiqvisHTXLgFQT_52p3Wwx2Mw','259110','2023-07-23 15:05:49','2024-01-24 16:39:32'),
	(3,'ru','Робокасса','Робокасса (для самозанятых, ИП, ООО)','руб.','RUB','robokassa','inactive',0,30,'U8w0F1YKG1kFrr9RTKew:XSdz5bqyQ19f90byVdzS','chatgptru','2023-07-23 15:05:49','2024-01-12 14:09:12'),
	(4,'ru','Lava','Lava (для самозанятых, ИП, ООО)','руб.','RUB','lava','inactive',0,30,'8bdf8dab7817d65a63cb8ae98bebd002fa753f21','79ef11f4-a7ab-4654-89d1-d42d71b292a1','2023-07-23 15:05:49','2024-01-24 16:39:31');

/*!40000 ALTER TABLE `payment_providers` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table payments
# ------------------------------------------------------------

DROP TABLE IF EXISTS `payments`;

CREATE TABLE `payments` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `from_user_id` int NOT NULL DEFAULT '0',
  `user_id` int NOT NULL,
  `tariff_id` int NOT NULL,
  `payment_provider_id` int NOT NULL,
  `amount` float NOT NULL,
  `currency` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'rub',
  `proxy_amount` int NOT NULL DEFAULT '0',
  `xlink` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '-',
  `label` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'PremiumAiBot',
  `payment_data` json DEFAULT NULL,
  `type` enum('tx','promocode','refferal','zeroing','user','bonus','burn','refferal_cash','burn_bonus') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'tx',
  `status` enum('new','pending','success','declined') NOT NULL DEFAULT 'new',
  `close` tinyint(1) NOT NULL DEFAULT '0',
  `expires_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DELIMITER ;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`%` */ /*!50003 TRIGGER `zeroing_baalance_with_type` BEFORE INSERT ON `payments` FOR EACH ROW BEGIN
	DECLARE tokens INT;
    IF NEW.type IN ('zeroing') THEN
    	SELECT balance INTO tokens FROM users WHERE id = NEW.user_id;
        UPDATE users SET balance = 0 WHERE id = NEW.user_id;
        SET	NEW.proxy_amount = tokens;
    END IF;
END */;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`%` */ /*!50003 TRIGGER `incr_refferal_payment` BEFORE INSERT ON `payments` FOR EACH ROW BEGIN
    IF NEW.type = 'refferal' AND NEW.status = 'success' THEN
        UPDATE users SET balance = balance + NEW.proxy_amount WHERE id = NEW.user_id;
        SET NEW.close = 1;
    END IF;
END */;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`%` */ /*!50003 TRIGGER `incr_balance_user_with_user_type` BEFORE INSERT ON `payments` FOR EACH ROW BEGIN
    IF NEW.type IN ('user', 'bonus') AND NEW.status = 'success' AND NEW.close = 0 THEN
        UPDATE users SET balance = balance + NEW.proxy_amount WHERE id = NEW.user_id;
        SET NEW.close = 1;
    END IF;
END */;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`%` */ /*!50003 TRIGGER `incr_balance_with_success_status` BEFORE UPDATE ON `payments` FOR EACH ROW BEGIN
    IF NEW.status = 'success' AND NEW.close = 1 THEN
        UPDATE users SET balance = balance + NEW.proxy_amount WHERE id = NEW.user_id;
        SET NEW.close = 1;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;


# Dump of table promocodes
# ------------------------------------------------------------

DROP TABLE IF EXISTS `promocodes`;

CREATE TABLE `promocodes` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `code` varchar(32) DEFAULT NULL,
  `usage` int NOT NULL DEFAULT '0',
  `amount` int DEFAULT NULL,
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active',
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DELIMITER ;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`%` */ /*!50003 TRIGGER `update_promocode` BEFORE UPDATE ON `promocodes` FOR EACH ROW BEGIN
    IF NEW.usage <= 0 THEN
        SET NEW.usage = 0;
        SET NEW.status = 'inactive';
    END IF;
END */;;
DELIMITER ;
/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;


# Dump of table requests
# ------------------------------------------------------------

DROP TABLE IF EXISTS `requests`;

CREATE TABLE `requests` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `dialog_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  `message` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `answer` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `prompt_tokens` int NOT NULL DEFAULT '0',
  `completion_tokens` int NOT NULL DEFAULT '0',
  `type` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'chatgpt',
  `total_tokens` int NOT NULL DEFAULT '0',
  `unlimited` tinyint(1) NOT NULL DEFAULT '0',
  `request_type` varchar(112) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `status` enum('new','proccess','success','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'success',
  `is_sub` tinyint(1) NOT NULL DEFAULT '0',
  `is_deleted` int NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL,
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DELIMITER ;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`%` */ /*!50003 TRIGGER `update_tokens_trigger` AFTER INSERT ON `requests` FOR EACH ROW BEGIN    
    IF NEW.unlimited IN (0) THEN
        UPDATE users SET balance = balance - NEW.total_tokens WHERE id = NEW.user_id;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;


# Dump of table statistics
# ------------------------------------------------------------

DROP TABLE IF EXISTS `statistics`;

CREATE TABLE `statistics` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `section` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'home',
  `created_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



# Dump of table subscriptions
# ------------------------------------------------------------

DROP TABLE IF EXISTS `subscriptions`;

CREATE TABLE `subscriptions` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `provider_id` int NOT NULL DEFAULT '0',
  `tokens` int NOT NULL DEFAULT '0',
  `status` set('active','inactive') NOT NULL DEFAULT 'active',
  `autopayment` tinyint NOT NULL DEFAULT '0',
  `data` json DEFAULT NULL,
  `spent_nofity` tinyint NOT NULL DEFAULT '0',
  `tomorrow_notify` tinyint NOT NULL DEFAULT '0',
  `expires_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



# Dump of table tariffs
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tariffs`;

CREATE TABLE `tariffs` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL DEFAULT '0',
  `language_code` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'ru',
  `name` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '-',
  `tokens` int NOT NULL DEFAULT '0',
  `type` enum('tokens') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'tokens',
  `amount` float NOT NULL DEFAULT '0',
  `currency` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'rub',
  `secret_bonus` int NOT NULL DEFAULT '0',
  `days_before_burn` int NOT NULL DEFAULT '0',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL,
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `tariffs` WRITE;
/*!40000 ALTER TABLE `tariffs` DISABLE KEYS */;

INSERT INTO `tariffs` (`id`, `user_id`, `language_code`, `name`, `tokens`, `type`, `amount`, `currency`, `secret_bonus`, `days_before_burn`, `status`, `created_at`, `updated_at`)
VALUES
	(1,0,'ru','150,000 токенов',150000,'tokens',99,'rub',0,7,'active','2023-03-22 02:04:25','2024-01-24 12:02:11'),
	(2,0,'ru','250,000 токенов',250000,'tokens',189,'rub',0,14,'active','2023-03-22 02:04:25','2024-01-24 11:22:58'),
	(3,0,'ru','500,000 токенов',500000,'tokens',349,'rub',0,21,'active','2023-03-22 02:04:25','2024-01-24 11:23:04'),
	(6,0,'ru','1,000,000 токенов',1000000,'tokens',698,'rub',0,30,'active','2023-03-22 02:04:25','2024-01-24 11:23:10'),
	(16,0,'ru','150,000 токенов',150000,'tokens',149,'rub',0,0,'active','2023-03-22 02:04:25','2024-01-24 12:02:19'),
	(17,0,'ru','250,000 токенов',250000,'tokens',279,'rub',0,0,'active','2023-03-22 02:04:25','2024-01-24 11:22:58'),
	(18,0,'ru','500,000 токенов',500000,'tokens',519,'rub',0,0,'active','2023-03-22 02:04:25','2024-01-24 11:23:04'),
	(19,0,'ru','1,000,000 токенов',1000000,'tokens',999,'rub',0,0,'active','2023-03-22 02:04:25','2024-01-24 11:23:10');

/*!40000 ALTER TABLE `tariffs` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table users
# ------------------------------------------------------------

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `telegram_id` bigint NOT NULL,
  `reffer_id` int DEFAULT NULL,
  `type` varchar(56) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'user',
  `language_code` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT 'nill',
  `username` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `balance` bigint NOT NULL DEFAULT '0',
  `role` enum('user','admin','superuser','demo','blocked') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'user',
  `billing_information` tinyint(1) NOT NULL DEFAULT '1',
  `is_subscriber` tinyint(1) NOT NULL DEFAULT '0',
  `is_active` int NOT NULL DEFAULT '0',
  `is_superuser` tinyint(1) NOT NULL DEFAULT '0',
  `is_unlimited` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL,
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `telegram_id` (`telegram_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DELIMITER ;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`%` */ /*!50003 TRIGGER `update_superuser` BEFORE INSERT ON `users` FOR EACH ROW BEGIN
    IF NEW.id = 1 THEN
        SET NEW.role = 'admin';
        SET NEW.is_superuser = 1;
    END IF;
END */;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION" */;;
/*!50003 CREATE */ /*!50017 DEFINER=`root`@`%` */ /*!50003 TRIGGER `update_user_balance_with_zero` BEFORE UPDATE ON `users` FOR EACH ROW BEGIN
    IF NEW.balance < 0 THEN
        SET NEW.balance = 0;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;


# Dump of table wallets
# ------------------------------------------------------------

DROP TABLE IF EXISTS `wallets`;

CREATE TABLE `wallets` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `type` set('refferal_cash') NOT NULL DEFAULT 'refferal_cash',
  `currency` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `balance` float DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_user_id_type` (`user_id`,`type`,`currency`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;




--
-- Dumping routines (PROCEDURE) for database 'gdegaz'
--
DELIMITER ;;

# Dump of PROCEDURE activate_promocode
# ------------------------------------------------------------

/*!50003 DROP PROCEDURE IF EXISTS `activate_promocode` */;;
/*!50003 SET SESSION SQL_MODE="ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"*/;;
/*!50003 CREATE*/ /*!50020 DEFINER=`root`@`%`*/ /*!50003 PROCEDURE `activate_promocode`(IN user_id INT, IN promocode VARCHAR(128))
activate_promocode_block:BEGIN
		DECLARE promocode_usage INT;
		DECLARE promocode_amount INT;
		DECLARE promocodes_status ENUM('active', 'inactive');
		
		-- Извлекаю сумму и статус промокода
		SELECT `status`, `amount`, `usage` INTO promocodes_status, promocode_amount, promocode_usage FROM `promocodes` WHERE `code` = `promocode`;
		
		IF promocode_usage = 0 THEN
        UPDATE `promocodes` SET `status` = 'inactive' WHERE code = promocode;
   			LEAVE activate_promocode_block;
		END IF;
		
		-- Проверка активности промокода
		IF promocodes_status = 'inactive' THEN
   			LEAVE activate_promocode_block;
		END IF;
		
		-- Уменьшаю кол-во использованй промокода
		UPDATE `promocodes` SET `usage` = `usage` - 1 WHERE `code` = `promocode`;
		
		UPDATE users SET balance = balance + promocode_amount WHERE id = user_id;
		
		INSERT INTO `payments` (tariff_id, payment_provider_id, user_id, amount, proxy_amount, xlink, label, status, type, created_at) VALUES (
			0, 0, user_id, 0, `promocode_amount`, '-', promocode, 'success', 'promocode', NOW()
		);
		
	END */;;

/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;;
DELIMITER ;

/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
