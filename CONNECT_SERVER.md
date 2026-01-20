# Подключение к серверу

## Данные для подключения:
- IP: 85.155.125.173
- Пользователь: root
- Пароль: FoVM5LYhe9PYhLQEa0aIAUGioAatzg3Q

## Способ 1: Через PowerShell (встроенный SSH)

Открой PowerShell и выполни:

```powershell
ssh root@85.155.125.173
```

Когда попросит пароль, вставь:
```
FoVM5LYhe9PYhLQEa0aIAUGioAatzg3Q
```

При первом подключении спросит:
```
Are you sure you want to continue connecting (yes/no)?
```
Напиши: `yes`

## Способ 2: Через PuTTY (если нет SSH)

1. Скачай PuTTY: https://www.putty.org/
2. Запусти PuTTY
3. В поле "Host Name" введи: `85.155.125.173`
4. Port: `22`
5. Connection type: `SSH`
6. Нажми "Open"
7. Введи логин: `root`
8. Введи пароль: `FoVM5LYhe9PYhLQEa0aIAUGioAatzg3Q`

## После подключения

Ты увидишь что-то типа:
```
root@server:~#
```

Теперь можешь выполнять команды из DEPLOY_UBUNTU.md!

## Быстрый старт

После подключения выполни:

```bash
# 1. Обнови систему
apt update && apt upgrade -y

# 2. Установи Python и зависимости
apt install python3 python3-pip python3-venv screen -y

# 3. Создай папку для бота
mkdir -p /root/vpn_bot
cd /root/vpn_bot

# Теперь загрузи файлы с Windows (см. ниже)
```

## Загрузка файлов с Windows на сервер

### Вариант 1: Через SCP (в PowerShell на Windows)

```powershell
# Перейди в папку с ботом
cd C:\Users\xuza\Downloads\vpm

# Загрузи все файлы
scp -r * root@85.155.125.173:/root/vpn_bot/
```

Введи пароль когда попросит.

### Вариант 2: Через WinSCP (графический интерфейс)

1. Скачай WinSCP: https://winscp.net/
2. Запусти WinSCP
3. Заполни:
   - File protocol: `SCP`
   - Host name: `85.155.125.173`
   - Port: `22`
   - User name: `root`
   - Password: `FoVM5LYhe9PYhLQEa0aIAUGioAatzg3Q`
4. Нажми "Login"
5. Перетащи файлы из левой панели (Windows) в правую (сервер)
6. Загрузи в папку `/root/vpn_bot/`

## Отключение от сервера

```bash
exit
```

Или просто закрой окно.

## Если забыл отключиться от screen

```bash
# Посмотри активные сессии
screen -ls

# Подключись к сессии
screen -r vpn_bot

# Отключись правильно
# Нажми: Ctrl+A, затем D
```
