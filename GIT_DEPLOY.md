# Деплой через Git

## Что загружать в репозиторий:

### ✅ ЗАГРУЖАТЬ:
- `bot.py` - основной файл бота
- `config.py` - конфигурация
- `database.py` - работа с БД
- `xui_api.py` - API 3X-UI
- `crystalpay.py` - оплата
- `requirements.txt` - зависимости
- `.env.example` - пример настроек
- `README.md` - описание проекта
- `.gitignore` - исключения для git

### ❌ НЕ ЗАГРУЖАТЬ:
- `.env` - **СЕКРЕТНЫЕ ДАННЫЕ!**
- `vpn_bot.db` - база данных
- `__pycache__/` - кэш Python
- `venv/` - виртуальное окружение
- Тестовые скрипты

## Шаг 1: Создай репозиторий на GitHub

1. Зайди на https://github.com
2. Нажми "New repository"
3. Название: `vpn-telegram-bot` (или любое)
4. Сделай **Private** (чтобы никто не видел код)
5. Нажми "Create repository"

## Шаг 2: Загрузи код в репозиторий

На Windows (в PowerShell):

```powershell
# Перейди в папку с ботом
cd C:\Users\xuza\Downloads\vpm

# Инициализируй git (если еще не сделал)
git init

# Добавь все файлы (кроме тех что в .gitignore)
git add .

# Сделай первый коммит
git commit -m "Initial commit"

# Добавь удаленный репозиторий (замени на свой URL)
git remote add origin https://github.com/твой_username/vpn-telegram-bot.git

# Загрузи код
git push -u origin main
```

Если попросит логин/пароль:
- Используй Personal Access Token вместо пароля
- Создай токен: GitHub → Settings → Developer settings → Personal access tokens → Generate new token

## Шаг 3: Загрузи на сервер через Git

На сервере:

```bash
# Подключись к серверу
ssh root@85.155.125.173

# Установи git (если нет)
apt install git -y

# Клонируй репозиторий
cd /root
git clone https://github.com/твой_username/vpn-telegram-bot.git vpn_bot
cd vpn_bot

# Создай .env файл вручную
nano .env
```

Вставь свои данные:
```env
TELEGRAM_BOT_TOKEN=8528861698:AAE9Mr8fx8mt85JD14Koj-VvbF7xVjHQegE
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

```bash
# Установи зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Запусти бота
python3 bot.py
```

## Шаг 4: Обновление бота

Когда изменишь код на Windows:

```powershell
# На Windows
cd C:\Users\xuza\Downloads\vpm

# Добавь изменения
git add .
git commit -m "Описание изменений"
git push
```

На сервере:

```bash
# Останови бота
sudo systemctl stop vpn_bot
# или Ctrl+C если через screen

# Обнови код
cd /root/vpn_bot
git pull

# Перезапусти бота
sudo systemctl start vpn_bot
# или python3 bot.py
```

## Альтернатива: Без Git (через SCP)

Если не хочешь возиться с Git:

```powershell
# На Windows - загрузи файлы напрямую
cd C:\Users\xuza\Downloads\vpm

# Загрузи только нужные файлы
scp bot.py config.py database.py xui_api.py crystalpay.py requirements.txt root@85.155.125.173:/root/vpn_bot/

# Загрузи .env отдельно
scp .env root@85.155.125.173:/root/vpn_bot/
```

## Рекомендация

**Используй Git** - это удобнее:
- ✅ История изменений
- ✅ Легко откатиться к старой версии
- ✅ Можно работать с разных компьютеров
- ✅ Автоматические бэкапы кода

Но **НЕ ЗАГРУЖАЙ .env в Git** - это секретные данные!

## Безопасность

Если случайно загрузил .env в Git:

```powershell
# Удали файл из истории
git rm --cached .env
git commit -m "Remove .env from git"
git push

# Смени все пароли и токены!
# Старые данные остались в истории Git
```

Лучше сразу сделай репозиторий **Private** и не загружай секреты.
