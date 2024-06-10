1)

# UBUNTU
`apt update`
`sudo apt install python`
`sudo apt install python3-pip -y && sudo apt install -y python3-venv -y && sudo apt install mysql-server -y && sudo apt install redis -y && sudo apt install supervisor -y && sudo apt install nginx -y`

2)

# Создание директории
`cd ../var/`
`mkdir projects`
_Импортировать папку с ботом через sftp/scp/github_

# Настройки main.ini
1. Вписать апи-ключ от телеграм бота в директиве [default] в параметре token;

# MYSQL
`mysql -u root`
```
CREATE DATABASE premiumaibot;
CREATE USER 'root'@'%' IDENTIFIED BY 'NeTyJy2058#';
CREATE USER 'premiumai'@'%' IDENTIFIED BY 'NeTyJy2058#';
GRANT ALL PRIVILEGES ON `premiumaibot`.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON `premiumaibot`.* TO 'premiumai'@'%';
GRANT SUPER ON *.* TO 'premiumai'@'%';
FLUSH PRIVILEGES;
```

## Импортируем базу
`cd /var/projects/PremiumAiBot/data/sql/`
`mysql -u premiumai -p -D premiumaibot < gpt.sql`

# For dump
`sudo mysqldump -u root -p premiumaibot > gpt.sql`

3)
# SUPERVISOR ADD CONFIG
`ln -s /var/projects/PremiumAiBot/config/supervisor/PremiumAiBot.conf /etc/supervisor/conf.d/`

4)

`mkdir certificates`
`cd ../var/projects/PremiumAiBot/config/certificates/`

`openssl req -newkey rsa:2048 -sha256 -nodes -x509 -days 365 \
-keyout private.key \
-out public.crt \
-subj "/C=RU/ST=Saint-Petersburg/L=Saint-Petersburg/O=PremiumAiBot Inc/CN=80.90.178.37"`


`openssl x509 -in public.crt -out public.pem -outform PEM`

# NGINX

## Cамоподписанный
`ln -s /var/projects/PremiumAiBot/config/nginx/PremiumAiBotSelf.conf /etc/nginx/sites-enabled/`

5)

`cd ../var/projects/PremiumAiBot/`
`python -m venv env`
`source env/bin/activate`
`pip install -r requirements.txt`

6)
Финальный тест

`python polling.py`

Должно выдать ОК и бот должен отреагировать приветствием.

# Supervisor
`supervisorctl update`
`supervisorctl start premium_ai_bot`

# Nginx
`systemctl restart nginx`

7)
# Делаем себя админом и супер пользователем
`mysql -u root`
```
use premiumaibot;
update users set role = 'admin' where id = 1;
update users set role = 'admin', is_superuser = 1 where id = 2;
```
