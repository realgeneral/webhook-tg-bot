-- MySQL dump 10.13  Distrib 8.0.36, for Linux (x86_64)
--
-- Host: localhost    Database: premiumaibot
-- ------------------------------------------------------
-- Server version	8.0.36-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `pages`
--

DROP TABLE IF EXISTS `pages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pages`
--

LOCK TABLES `pages` WRITE;
/*!40000 ALTER TABLE `pages` DISABLE KEYS */;
INSERT INTO `pages` VALUES (1,1,0,'ru','faq','Помощь','❔Выберите интересующий вас раздел\n\n',NULL,'2023-07-31 08:27:50','2023-07-19 17:27:41'),(2,1,1,'ru','tokens','🔹 Токены','*🔹 Что такое токен?*\n\nТокен — это валюта нашего бота. С помощью неё вы можете общаться с ChatGPT, генерировать изображения через DALL-E и MidJourney.\n\n*🔹 Как тратятся токены в ChatGPT?*\n— 1 токен ≈ 1 символ на русском\n— 1 токен ≈ 4 символам на английском\n\n*🔹 Как они тратятся в DALL-E?*\n— 1000 токенов = 1 изображение\n\n*🔹 У меня не осталось токенов, что делать?*\n— Вы можете купить токены в разделе «💎 Магазин». /shop\n— Вы можете следить за постами в наших каналах, находить в постах промокоды и активировать их в разделе  «💎 Магазин»  по кнопке «🔢 Активировать промокод» и пользоваться ботом бесплатно. Попробуйте найти их по хештегу #PROMO. Промокоды многоразовые и вы точно сможете их активировать.\n\n❗️ Во всех разделах бот уведомляет вас о том, сколько токенов было затрачено и/или будет затрачено и сколько токенов осталось.',NULL,'2023-08-08 08:16:02','2023-07-19 17:27:41'),(3,1,1,'ru','payments','💎 Платежи','*Оплата тарифов*\n\nВсе наши тарифы представлены в разделе «💎 Магазин». /shop\n\n⌛ Токены зачисляются на ваш баланс автоматически в течении 5 минут после оплаты.\n\n❗️ В случае если вы оплатили, но токены не зачислились в течении 5 минут, напишите администратору по кнопке ниже.\n\n*Статусы платежей:*\n🆕 — новый, ожидает проверки;\n⏳ — ожидает платёж и проверяет оплату;\n🟢 — платёж завершен;\n🔴 — платёж отклонён или истекло время ожидания.\n\n*Типы платежей:*\n*1. Оплата ...* — оплата тарифа или услуги;\n*2. Промокод ...* — был активирован промокод;\n*3. Реферальная программа* — начисление токенов за нового реферала или за оплату тарифа;\n*4. Обнуление баланса* — происходит в случае мошенничества или блокировки аккаунта за неоднократное нарушение правил сервиса.',NULL,'2023-08-08 07:21:18','2023-07-19 17:27:41'),(4,1,1,'ru','roles','💬  ChatGPT','*💬 ChatGPT*. Ответы на часто задаваемые вопросы.\n\n*— У меня было 50 токенов на балансе, но мой запрос всё равно обработался и забрал больше, почему?*\nНе волнуйтесь, это нормально. Мы даём право на последний бесплатный запрос. Это значит, что если запрос к чату затратил больше токенов, чем у вас есть, то бот спишет только те, что у вас остались и не будет уводить ваш баланс токенов в минус.\n\n*— Что за параметр «Включить/выключить показ затрат» в диалоге с ChatGPT?*\nВ включенном состоянии этот параметр  отправляет вам информацию о стоимости каждого запроса, сделанного Вами в рамках диалога или вызова функции /gpt _ваш запрос_.\n\n*— Почему чат сохраняет не всю историю, а только последние несколько сообщений?*\nСистема хранит только последние 6 сообщений в чате Это сделано для экономии токенов и избежания ошибок со стороны OpenAi. _Помните, диалог с сохранением истории тратит намного больше токенов, чем без сохранения._',NULL,'2023-08-08 07:50:28','2023-07-19 17:27:41'),(5,1,1,'ru','ads','💵 Сотрудничество','По рекламе/сотрудничеству пишите по контактам ниже.\n\nЕвгений — https://t.me/Social\\_Style',NULL,'2024-02-05 11:51:06','2023-07-19 17:27:41'),(12,1,0,'en','faq','Help','❔Choose\n\n',NULL,'2023-08-02 07:38:34','2023-07-19 17:27:41'),(13,1,12,'en','tokens','🔹 Tokens','Tokens',NULL,'2023-08-02 08:07:01','2023-07-19 17:27:41'),(14,1,12,'en','payments','💎 Payments','Tarrifs',NULL,'2023-08-08 07:12:27','2023-07-19 17:27:41'),(15,1,12,'en','roles','💬  ChatGPT','*💬 ChatGPT*. Ответы на часто задаваемые вопросы.\n\n*— У меня было 50 токенов на балансе, но мой запрос всё равно обработался и забрал больше, почему?*\nНе волнуйтесь, это нормально. Мы даём право на последний бесплатный запрос. Это значит, что если запрос к чату затратил больше токенов, чем у вас есть, то бот спишет только те, что у вас остались и не будет уводить ваш баланс токенов в минус.\n\n*— Что за параметр «Включить/выключить показ затрат» в диалоге с ChatGPT?*\nВ включенном состоянии этот параметр  отправляет вам информацию о стоимости каждого запроса, сделанного Вами в рамках диалога или вызова функции /gpt _ваш запрос_.\n\n*— Почему чат сохраняет не всю историю, а только последние несколько сообщений?*\nСистема хранит только последние 6 сообщений в чате Это сделано для экономии токенов и избежания ошибок со стороны OpenAi. _Помните, диалог с сохранением истории тратит намного больше токенов, чем без сохранения._',NULL,'2023-08-08 07:50:24','2023-07-19 17:27:41'),(16,1,12,'en','ads','💵 Ads','Рекламочкка',NULL,'2023-08-02 08:07:04','2023-07-19 17:27:41'),(17,1,1,'ru','data','📖 Политика хранения данных','*📖 Политика хранения данных*\n\nМы трепетно относимся к данным наших пользователей и поэтому решили написать эту политику, чтобы вы были уведомлены, как мы храним данные. \n\nАдмиинстрация бота имеет доступ только к управлению вашим аккаунтом (блокировка, выдача определённых прав и иные сервисные функции), но прав на доступ к истории ваших запросов у неё нет.\n\nНиже приведён перечь данных, которые мы временно храним на своих серверах.\n\n*ChatGPT*\n1. История ваших запросов в диалоге хранится на сервере до момента, пока вы не выполните очистку диалога по команде «/clear» или «Очистить историю».\n2. История ваших запросов через команду «/gpt _вопрос_» или «@PremiumAiBot _запрос_» хранится до конца суток и автоматически очищается системой.\n\n*DALL-E*\nИстория ваших запросов  хранится до конца суток и автоматически очищается системой. Система хранит информацию запрос-ссылки (на сервере OpenAi). \n\n❗️*Система очищает только вопрос-ответ и хранит информацию о потраченных токенах за запрос для извлечения статистики по тратам.*',NULL,'2023-08-22 07:22:49','2023-07-19 17:27:41'),(18,1,12,'en','data','📖 Data storage policy','*📖 Data storage policy*\n\nWe care about our users\' data, so we decided to write this policy so that you can be informed about how we store data. \n\nThe bot administration only has access to your account management (blocking, granting certain rights and other service functions), but they do not have access to your request history.\n\nBelow is a list of data that we temporarily store on our servers.\n\n*ChatGPT*\n1. The history of your requests in the dialog is stored on the server until you clear the dialog using the command \"/clear\" or \"Clear history\".\n2. The history of your requests via the command \"/gpt question\" or \"@PremiumAiBot request\" is stored until the end of the day and is automatically cleared by the system.\n\n*DALL-E.*\nYour query history is stored until the end of the day and is automatically cleared by the system. The system stores the query-reference information (on the OpenAi server). \n\n❗️System clears only the query-reply and stores information about the tokens spent per query to extract statistics on spending.',NULL,'2023-08-22 07:24:58','2023-07-19 17:27:41'),(19,1,1,'ru','policy_chargeback','Политика возвратов','Возвраты',NULL,'2023-08-08 08:14:42','2023-07-19 17:27:41'),(20,1,1,'ru','offer','Оферта','Оферта',NULL,'2024-01-11 09:43:51','2023-07-19 17:27:41'),(21,1,1,'ru','terms','Пользовательское соглашение','Пользовательское соглашение',NULL,'2024-01-11 09:43:51','2023-07-19 17:27:41'),(22,1,0,'ru','home','Главная','🙋 <b>Привет, {first_name}!</b> У тебя есть <b>{amount:,} {balance}</b>, используй их для любой нейросети в нашем боте.\n\n💬 <b>ChatGPT</b> является мощнейшим искусственным интеллектом и с лёгкостью станет для тебя помощником, разберётся во множестве задач и вопросов, просто нажми на <b>🗯 Начать общение</b> и начинай общаться. Ты можешь присылать боту <b>голосовые сообщения</b>, <b>фотографии</b>, а он будет тебе отвечать на них. Если захочешь необычного общения, перейди в <b>💬 Диалоги ChatGPT</b>\n\n🌌 <b>DALL·E 3 и 🖌 Stable Diffusion</b> нарисуют качественные картинки под любые нужды. Выбери, что по душе и отправь боту сообщение с запросом и в ответ он отправит тебе фото. Каждая нейросеть имеет свои особенности, <i>особый функционал</i> и стоимость.\n\n— Если у вас возникли трудности при использовании нейросетей и бота или вы хотите узнать о его *возможностях* больше, перейдите в раздел <b>«🤔 Помощь»</b> по кнопке или команде /faq.',NULL,'2024-04-10 06:02:59','2023-07-19 19:57:41');
/*!40000 ALTER TABLE `pages` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-05-14 17:23:51
