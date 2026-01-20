# Деплой бота на Ubuntu Server 24.04 LTS

**Сервер:** 85.155.125.173  
**Пользователь:** root  
**Пароль:** FoVM5LYhe9PYhLQEa0aIAUGioAatzg3Q  
**Метод запуска:** screen

## 1. Подготовка сервера (уже сделано)

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python 3 и pip
sudo apt install python3 python3-pip python3-venv -y

# Устанавливаем git
sudo apt install git -y

# Устанавливаем screen
sudo apt install screen -y
```

## 2. Первоначальная загрузка (уже сделано)

```bash
cd /root/
git clone your_repo_url vpn_bot
cd vpn_bot
```

### Вариант Б: Через SCP с Windows
На Windows (в PowerShell):
```powershell
# Перейди в папку сботом
cd C:\Users\xuza\Downloads\vpm

# Загрузи файлы на сервер (замени IP и путь)
scp -r * user@your_server_ip:/home/user/vpn_bot/
```

### Вариант В: Через SFTP (FileZilla, WinSCP)
1. Подключись к серверу через SFTP
2. Загрузи все файлы в папку `/home/user/vpn_bot/`

## 3. Установка зависимостей

```bash
cd /home/user/vpn_bot

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

## 4. Настройка .env файла

```bash
# Редактируем .env файл
nano .env
```

Проверь что все данные правильные:
```env
TELEGRAM_BOT_TOKEN=твой_токен
XUI_PANEL_URL=https://vpnshi.mooo.com/qwoBawtltY/
XUI_USERNAME=xuza
XUI_PASSWORD=Govnoed_66228
ADMIN_ID=8145856236
SUPPORT_USERNAME=stewvpn_support
CRYSTALPAY_NAME=stew
CRYSTALPAY_SECRET1=c128510eda1ee07aad4224c45ab62f96396a90da
CRYSTALPAY_SECRET2=338c28eb84eaa29fed512f2776d1b9ef22795437
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

## 5. Запуск бота

### Вариант А: Через screen (рекомендуется)
```bash
# Создаем новую screen сессию
screen -S vpn_bot

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем бота
python3 bot.py

# Отключаемся от screen (бот продолжит работать)
# Нажми: Ctrl+A, затем D
```

Полезные команды screen:
```bash
# Посмотреть список сессий
screen -ls

# Подключиться к сессии
screen -r vpn_bot

# Убить сессию
screen -X -S vpn_bot quit
```

### Вариант Б: Через systemd (автозапуск)
```bash
# Создаем systemd service
sudo nano /etc/systemd/system/vpn_bot.service
```

Вставь:
```ini
[Unit]
Description=VPN Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/vpn_bot
Environment="PATH=/home/your_user/vpn_bot/venv/bin"
ExecStart=/home/your_user/vpn_bot/venv/bin/python3 /home/your_user/vpn_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Замени `your_user` на твоего пользователя!

```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Запускаем бота
sudo systemctl start vpn_bot

# Включаем автозапуск
sudo systemctl enable vpn_bot

# Проверяем статус
sudo systemctl status vpn_bot

# Смотрим логи
sudo journalctl -u vpn_bot -f
```

Полезные команды systemd:
```bash
# Остановить бота
sudo systemctl stop vpn_bot

# Перезапустить бота
sudo systemctl restart vpn_bot

# Посмотреть логи
sudo journalctl -u vpn_bot -n 100

# Следить за логами в реальном времени
sudo journalctl -u vpn_bot -f
```

## 6. Проверка работы

```bash
# Проверь что бот запущен
ps aux | grep bot.py

# Проверь логи
tail -f /home/user/vpn_bot/bot.log  # если настроил логирование в файл
```

## 7. Обновление бота (ОСНОВНАЯ ИНСТРУКЦИЯ)

### На Windows (закоммить изменения):
```bash
# Через GitHub Desktop или git bash:
git add .
git commit -m "Update bot"
git push
```

### На сервере (обновить и перезапустить):
```bash
# 1. Подключись к серверу
ssh root@85.155.125.173
# Пароль: FoVM5LYhe9PYhLQEa0aIAUGioAatzg3Q

# 2. Перейди в папку бота
cd /root/vpn_bot

# 3. Останови бота (подключись к screen)
screen -r vpn_bot
# Нажми Ctrl+C чтобы остановить бота

# 4. Обнови файлы с GitHub
git pull

# 5. Обнови зависимости (если нужно)
pip install -r requirements.txt

# 6. Запусти бота снова
python3 bot.py

# 7. Отключись от screen (бот продолжит работать)
# Нажми: Ctrl+A, затем D
```

### Быстрая команда (если бот уже запущен):
```bash
ssh root@85.155.125.173 "cd /root/vpn_bot && screen -X -S vpn_bot quit && git pull && screen -dmS vpn_bot python3 bot.py"
```

## 8. Резервное копирование

```bash
# Создай скрипт для бэкапа
nano /home/user/backup_bot.sh
```

Вставь:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/user/backups"
BOT_DIR="/home/user/vpn_bot"

mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp $BOT_DIR/vpn_bot.db $BACKUP_DIR/vpn_bot_$DATE.db

# Бэкап .env
cp $BOT_DIR/.env $BACKUP_DIR/.env_$DATE

# Удаляем старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "vpn_bot_*.db" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Делаем скрипт исполняемым
chmod +x /home/user/backup_bot.sh

# Добавляем в cron (каждый день в 3:00)
crontab -e
```

Добавь строку:
```
0 3 * * * /home/user/backup_bot.sh >> /home/user/backup.log 2>&1
```

## 9. Мониторинг

```bash
# Установи htop для мониторинга
sudo apt install htop -y

# Запусти htop
htop

# Найди процесс bot.py и смотри использование ресурсов
```

## 10. Безопасность

```bash
# Настрой firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw enable

# Ограничь доступ к .env файлу
chmod 600 /home/user/vpn_bot/.env

# Создай отдельного пользователя для бота (опционально)
sudo adduser botuser
sudo su - botuser
# Повтори установку от имени botuser
```

## Troubleshooting

### Бот не запускается
```bash
# Проверь логи
sudo journalctl -u vpn_bot -n 50

# Проверь права на файлы
ls -la /home/user/vpn_bot/

# Проверь что виртуальное окружение активно
which python3
```

### Бот падает
```bash
# Проверь логи ошибок
sudo journalctl -u vpn_bot -p err

# Проверь что все зависимости установлены
source venv/bin/activate
pip list
```

### База данных заблокирована
```bash
# Проверь что нет других процессов
ps aux | grep bot.py

# Убей зависшие процессы
pkill -f bot.py

# Перезапусти бота
sudo systemctl restart vpn_bot
```

## Полезные команды

```bash
# Посмотреть использование диска
df -h

# Посмотреть размер базы данных
du -h /home/user/vpn_bot/vpn_bot.db

# Посмотреть сетевые соединения
netstat -tulpn | grep python

# Посмотреть открытые файлы
lsof -p $(pgrep -f bot.py)
```

## Готово!

Бот запущен и работает в фоне. Он будет автоматически перезапускаться при падении и запускаться при перезагрузке сервера.
