# #!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import asyncio
import secrets
import json
import sys

# Исправление кодировки для Windows консоли
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, PreCheckoutQueryHandler
import config
import database
from xui_api import XUIClient
from crystalpay import CrystalPayAPI
from datetime import datetime
from subscription_check import check_user_subscription
    
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Отключаем подробные логи httpx и requests
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

xui_client = XUIClient()
crystalpay_client = None
if config.CRYSTALPAY_NAME and config.CRYSTALPAY_SECRET1 and config.CRYSTALPAY_SECRET2:
    crystalpay_client = CrystalPayAPI(config.CRYSTALPAY_NAME, config.CRYSTALPAY_SECRET1, config.CRYSTALPAY_SECRET2)

user_states = {}
call_admin_cooldown = {}  # Хранит время последнего вызова админа для каждого пользователя

# ===== CHANNEL SUBSCRIPTION CHECK =====

async def check_subscription(user_id, bot_instance):
    """Проверка подписки на канал"""
    return await check_user_subscription(user_id, bot_instance)

# ===== MAIN MENU =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Проверка бана
    if await database.is_banned(user.id):
        await update.message.reply_text("You are banned")
        return
    
    await database.add_user(user.id, user.username)
    
    # Check channel subscription
    if not await check_subscription(user.id, context.bot):
        text = "Для использования бота необходимо подписаться на канал!\n\n" + \
               f"Канал: {config.REQUIRED_CHANNEL}\n\n" + \
               "После подписки нажмите кнопку ниже для проверки."
        keyboard = [
            [InlineKeyboardButton("Подписаться", url=f'https://t.me/{config.REQUIRED_CHANNEL.replace("@", "")}')],
            [InlineKeyboardButton("Я подписался", callback_data='check_sub')]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if context.args and context.args[0].isdigit():
        referrer_id = int(context.args[0])
        if referrer_id != user.id:
            await database.set_referrer(user.id, referrer_id)
    
    # Проверка согласия с политикой
    if not await database.has_agreed_policy(user.id):
        text = (
            f"👋 Добро пожаловать, {user.first_name}!\n\n"
            "🚀 STEWVPN - быстрый и надёжный VPN сервис\n\n"
            "Для продолжения необходимо принять Политику конфиденциальности и Условия использования."
        )
        keyboard = [
            [InlineKeyboardButton("📄 Прочитать", url='https://telegra.ph/Politika-konfidencialnosti-i-Usloviya-ispolzovaniya-VPN-servisa-01-15')],
            [InlineKeyboardButton("✅ Принимаю", callback_data='agree_policy')]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    await show_welcome(update, user)

async def show_welcome(update, user):
    text = (
        f"👋 Добро пожаловать, {user.first_name}!\n\n"
        "🚀 STEWVPN - быстрый и надёжный VPN сервис\n\n"
        "✨ Наши возможности:\n"
        "✅ Обход White List блокировок\n"
        "🎬 YouTube без рекламы\n"
        "⚡️ Низкий пинг для игр и потокового вещания\n"
        "🚄 Скорость без ограничений\n"
        "🛡️ Встроенный блокировщик рекламы\n"
        "🔒 Защита приватности и безопасность\n"
        "📱 Поддержка всех устройств\n\n"
        "И многое другое!\n\n"
        "Здесь вы можете купить VLESS ключи для безопасного и свободного интернета.\n\n"
        "Выберите действие:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛍 Купить ключ", callback_data='buy'),
         InlineKeyboardButton("🔑 Мои ключи", callback_data='my_keys')],
        [InlineKeyboardButton("💰 Баланс", callback_data='balance'),
         InlineKeyboardButton("❤️ Поддержка", callback_data='support')],
        [InlineKeyboardButton("🎁 Пробный ключ", callback_data='trial'),
         InlineKeyboardButton("🎟 Промокод", callback_data='promo')],
        [InlineKeyboardButton("👥 Реферальная система", callback_data='referral')]
    ]
    
    # Кнопка админки для админов
    if await database.is_admin(user.id):
        keyboard.append([InlineKeyboardButton("🔧 Админ панель", callback_data='admin')])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_main_menu(query):
    text = (
        "👋 Главное меню\n\n"
        "🚀 STEWVPN - быстрый и надёжный VPN\n\n"
        "Выберите действие:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛍 Купить ключ", callback_data='buy'),
         InlineKeyboardButton("🔑 Мои ключи", callback_data='my_keys')],
        [InlineKeyboardButton("💰 Баланс", callback_data='balance'),
         InlineKeyboardButton("❤️ Поддержка", callback_data='support')],
        [InlineKeyboardButton("🎁 Пробный ключ", callback_data='trial'),
         InlineKeyboardButton("🎟 Промокод", callback_data='promo')],
        [InlineKeyboardButton("👥 Реферальная система", callback_data='referral')]
    ]
    
    # Добавляем кнопку админ панели для админов
    if await database.is_admin(query.from_user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Админ панель", callback_data='admin')])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== BUTTON HANDLER =====

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    try:
        # Check subscription
        if data == 'check_sub':
            if await check_subscription(query.from_user.id, context.bot):
                await query.edit_message_text("Отлично! Подписка подтверждена.\n\nТеперь нажмите /start для продолжения.")
            else:
                await query.answer("Вы еще не подписались на канал!", show_alert=True)
            return
        
        # Policy agreement
        if data == 'agree_policy':
            await database.set_agreed_policy(query.from_user.id)
            await query.edit_message_text("✅ Спасибо! Теперь нажмите /start для продолжения.")
            return
        
        # Main
        if data == 'back_main':
            await show_main_menu(query)
        elif data == 'buy':
            await show_plans(query)
        elif data == 'my_keys':
            await show_my_keys(query)
        elif data == 'balance':
            await show_balance(query)
        elif data == 'support':
            await show_support(query)
        elif data == 'trial':
            await get_trial(query)
        elif data == 'promo':
            await show_promo(query)
        elif data == 'referral':
            await show_referral(query)
        elif data.startswith('plan_'):
            await process_purchase(query, data.replace('plan_', ''))
        elif data.startswith('device_'):
            await show_device_instructions(query, data.replace('device_', ''))
        elif data.startswith('key_'):
            await show_key_details(query, int(data.replace('key_', '')))
        
        # Admin
        elif data == 'admin':
            await show_admin_menu(query)
        elif data == 'admin_users':
            await admin_users(query)
        elif data == 'admin_promos':
            await admin_promos(query)
        elif data == 'admin_stats':
            await admin_stats_menu(query)
        elif data == 'admin_add_promo':
            await admin_add_promo_start(query)
        elif data.startswith('admin_user_keys_'):
            await admin_user_keys(query, int(data.replace('admin_user_keys_', '')))
        elif data.startswith('admin_user_'):
            await admin_user_details(query, int(data.replace('admin_user_', '')))
        elif data.startswith('admin_reset_trial_'):
            await admin_reset_trial(query, int(data.replace('admin_reset_trial_', '')))
        elif data.startswith('admin_set_balance_'):
            await admin_set_balance_start(query, int(data.replace('admin_set_balance_', '')))
        elif data.startswith('admin_del_promo_'):
            await admin_delete_promo(query, data.replace('admin_del_promo_', ''))
        elif data == 'admin_admins':
            await admin_admins_list(query)
        elif data.startswith('admin_add_admin_'):
            await admin_add_admin_start(query)
        elif data.startswith('admin_remove_admin_'):
            await admin_remove_admin(query, int(data.replace('admin_remove_admin_', '')))
        elif data.startswith('admin_ban_'):
            await admin_ban_user(query, int(data.replace('admin_ban_', '')))
        elif data.startswith('admin_unban_'):
            await admin_unban_user(query, int(data.replace('admin_unban_', '')))
        elif data.startswith('admin_del_key_'):
            await admin_delete_key(query, int(data.replace('admin_del_key_', '')))
        elif data == 'admin_cleanup':
            await admin_manual_cleanup(query)
        
        # Boosty payment confirmation
        elif data.startswith('confirm_payment_'):
            await admin_confirm_payment(query, int(data.replace('confirm_payment_', '')))
        elif data.startswith('boosty_plan_'):
            # Формат: boosty_plan_USER_ID_PLAN_ID
            parts = data.replace('boosty_plan_', '').split('_')
            user_id = int(parts[0])
            plan_id = '_'.join(parts[1:])  # Собираем plan_id обратно (например 1_month)
            await admin_process_boosty_payment(query, user_id, plan_id, context)
        
        # Stars payment
        elif data == 'pay_stars':
            await show_stars_plans(query)
        elif data.startswith('stars_buy_'):
            await send_stars_invoice(query, data.replace('stars_buy_', ''))
        
        # CrystalPay
        elif data == 'pay_card':
            await show_crystalpay_amounts(query)
        elif data.startswith('crystal_amount_'):
            await create_crystalpay_payment(query, int(data.replace('crystal_amount_', '')))
        elif data.startswith('crystal_check_'):
            await check_crystalpay_payment(query, data.replace('crystal_check_', ''))
        elif data == 'call_admin':
            await call_admin(query, context)
    except Exception as e:
        import traceback
        full_error = traceback.format_exc()
        logger.error(f"Button error: {e}")
        logger.error(f"Full traceback:\n{full_error}")
        try:
            await query.edit_message_text(f"❌ Ошибка: {e}")
        except:
            try:
                await query.message.reply_text(f"❌ Ошибка: {e}")
            except:
                pass

# ===== USER FUNCTIONS =====

async def show_plans(query):
    keyboard = []
    for plan_id, plan in config.PLANS.items():
        keyboard.append([InlineKeyboardButton(f"🇳🇱 {plan['name']} - {plan['price']}₽", callback_data=f'plan_{plan_id}')])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_main')])
    
    await query.edit_message_text("Выберите тариф:\n\n🇳🇱 Сервер: Нидерланды\n⚡️ Скорость: до 1 Гбит/с", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_my_keys(query):
    user_id = query.from_user.id
    subs = await database.get_user_subscriptions(user_id)
    
    if not subs:
        keyboard = [[InlineKeyboardButton("🛍 Купить ключ", callback_data='buy')], [InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]]
        await query.edit_message_text("У вас пока нет активных ключей", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    keyboard = []
    for sub in subs:
        name = "🔑 Пробный" if sub['plan_type'] == 'trial' else f"🔑 {config.PLANS.get(sub['plan_type'], {}).get('name', 'Ключ')}"
        keyboard.append([InlineKeyboardButton(name, callback_data=f'key_{sub["id"]}')])
    keyboard.append([InlineKeyboardButton("🛍 Купить ещё", callback_data='buy'), InlineKeyboardButton("⬅️ Назад", callback_data='back_main')])
    
    await query.edit_message_text(f"Ваши ключи ({len(subs)} активных):", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_key_details(query, key_id):
    user_id = query.from_user.id
    subs = await database.get_user_subscriptions(user_id)
    sub = next((s for s in subs if s['id'] == key_id), None)
    
    if not sub:
        await query.edit_message_text("Ключ не найден", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='my_keys')]]))
        return
    
    expires = datetime.fromisoformat(sub['expires_at'])
    text = f"🔑 Ваш ключ:\n\n`{sub['config_link']}`\n\nАктивен до: {expires.strftime('%d.%m.%Y %H:%M')}"
    
    keyboard = [
        [InlineKeyboardButton("📱 Android", callback_data='device_android')],
        [InlineKeyboardButton("🍎 iPhone", callback_data='device_iphone')],
        [InlineKeyboardButton("💻 Windows", callback_data='device_windows')],
        [InlineKeyboardButton("🍏 MacOS", callback_data='device_macos')],
        [InlineKeyboardButton("📺 Android TV", callback_data='device_tv')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='my_keys')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_balance(query):
    balance = await database.get_balance(query.from_user.id)
    text = f"💰 Ваш баланс: {balance}₽\n\nВыберите способ пополнения:"
    
    keyboard = [
        [InlineKeyboardButton("💳 По карте", callback_data='pay_card')],
        [InlineKeyboardButton("⭐️ Telegram Stars", callback_data='pay_stars')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_stars_plans(query):
    text = "⭐️ Оплата Telegram Stars\n\nВыберите тариф:"
    
    keyboard = []
    for plan_id, plan in config.PLANS.items():
        stars = plan.get('stars', 50)
        keyboard.append([InlineKeyboardButton(f"🇳🇱 {plan['name']} - {stars}⭐️", callback_data=f'stars_buy_{plan_id}')])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='balance')])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def send_stars_invoice(query, plan_id):
    plan = config.PLANS.get(plan_id)
    if not plan:
        await query.edit_message_text("❌ Тариф не найден")
        return
    
    stars = plan.get('stars', 50)
    
    await query.message.reply_invoice(
        title=f"STEWVPN - {plan['name']}",
        description=f"VPN подписка на {plan['name']}\n📊 Трафик: {plan['traffic_gb']} GB\n⏱ Срок: {plan['days']} дней",
        payload=f"vpn_{plan_id}_{query.from_user.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=plan['name'], amount=stars)]
    )

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    
    # Парсим payload: vpn_plan_id_user_id
    parts = payload.split('_')
    if len(parts) >= 3 and parts[0] == 'vpn':
        plan_id = parts[1] + '_' + parts[2] if len(parts) == 4 else parts[1]
        user_id = int(parts[-1])
        
        plan = config.PLANS.get(plan_id)
        if plan:
            try:
                # Создаем подписку
                username = update.message.from_user.username or f"user{user_id}"
                sub_id = secrets.token_urlsafe(12)
                
                # Создаем клиента для телефона (VLESS xhttp)
                result = xui_client.create_client(
                    email=f"{username}_phone",
                    sub_id=sub_id,
                    days=plan['days'],
                    traffic_gb=plan['traffic_gb'],
                    inbound_id=config.INBOUND_XHTTP
                )
                
                # Создаем клиента для ПК (Trojan gRPC)
                xui_client.create_client(
                    email=f"{username}_pc",
                    sub_id=sub_id,
                    days=plan['days'],
                    traffic_gb=plan['traffic_gb'],
                    inbound_id=config.INBOUND_TROJAN
                )
                
                if result:
                    await database.add_subscription(
                        user_id, plan_id, result['client_id'], result['config_link'], 
                        result['expires_at'], result['email']
                    )
                    sub_url = result['config_link']
                    
                    keyboard = [
                        [InlineKeyboardButton("📱 Android", callback_data='device_android')],
                        [InlineKeyboardButton("🍎 iPhone", callback_data='device_iphone')],
                        [InlineKeyboardButton("💻 Windows", callback_data='device_windows')],
                        [InlineKeyboardButton("🍏 MacOS", callback_data='device_macos')],
                        [InlineKeyboardButton("📺 Android TV", callback_data='device_tv')],
                        [InlineKeyboardButton("⬅️ В меню", callback_data='back_main')]
                    ]
                    
                    await update.message.reply_text(
                        f"✅ Оплата прошла успешно!\n\n🔑 Ваша подписка: {plan['name']}\n\n📲 Ссылка:\n`{sub_url}`\n\nВыберите устройство для инструкции:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                    
                    # Реферальный бонус
                    referrer = await database.get_referrer(user_id)
                    if referrer:
                        bonus = int(plan['price'] * 0.15)
                        await database.update_balance(referrer, bonus)
                else:
                    await update.message.reply_text("❌ Ошибка создания подписки. Обратитесь в поддержку.")
            except Exception as e:
                logger.error(f"Stars payment error: {e}")
                await update.message.reply_text(f"❌ Ошибка: {e}")

# ===== CRYSTALPAY PAYMENT =====

async def show_crystalpay_amounts(query):
    """Выбор суммы пополнения"""
    user = query.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    
    text = (
        "Hello! На данный момент выдача происходит через BOOSTY\n\n"
        "Инструкция:\n"
        "1. Зайти на Boosty (https://boosty.to/stewvpn)\n"
        "2. Зарегистрироваться\n"
        "3. Зайти на нашу страничку, выбрать подходящую подписку\n"
        "4. Оплатить\n"
        "5. Позвать администратора\n"
        f"6. Написать в чат на Boosty свой юзернейм: {username}\n\n"
        "Вся остальная инструкция будет указана после оплаты."
    )
    
    keyboard = [
        [InlineKeyboardButton("🔗 Открыть Boosty", url='https://boosty.to/stewvpn')],
        [InlineKeyboardButton("📞 Позвать админа", callback_data='call_admin')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='balance')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def create_crystalpay_payment(query, amount: int):
    """Создание платежа CrystalPay"""
    if not crystalpay_client:
        await query.edit_message_text("❌ CrystalPay не настроен", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='balance')]]))
        return
    
    user_id = query.from_user.id
    order_id = f"{user_id}_{secrets.token_hex(8)}"
    
    result = await crystalpay_client.create_payment(
        amount=amount,
        order_id=order_id,
        description=f"Пополнение баланса STEWVPN на {amount}₽"
    )
    
    if not result or result.get('error'):
        await query.edit_message_text(
            f"❌ Ошибка создания платежа\n\n{result.get('errors') if result else 'Неизвестная ошибка'}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='balance')]])
        )
        return
    
    payment_url = result.get('url')
    payment_id = result.get('id')
    
    # Сохраняем платеж в базу
    await database.add_payment(user_id, amount, 'balance', 'pending', payment_id)
    
    text = (
        f"💳 Счет на пополнение создан!\n\n"
        f"💰 Сумма: {amount}₽\n"
        f"🆔 ID платежа: `{payment_id}`\n\n"
        f"Нажмите кнопку ниже для оплаты.\n"
        f"После оплаты нажмите 'Проверить платеж'"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить", url=payment_url)],
        [InlineKeyboardButton("🔄 Проверить платеж", callback_data=f'crystal_check_{payment_id}')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='balance')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def check_crystalpay_payment(query, payment_id: str):
    """Проверка статуса платежа"""
    if not crystalpay_client:
        await query.answer("❌ CrystalPay не настроен")
        return
    
    result = await crystalpay_client.check_payment(payment_id)
    
    if not result:
        await query.answer("❌ Ошибка проверки платежа", show_alert=True)
        return
    
    status = result.get('state')
    amount = result.get('amount')
    
    if status == 'payed':
        # Платеж успешен
        user_id = query.from_user.id
        await database.update_balance(user_id, amount)
        await database.add_payment(user_id, amount, 'balance', 'completed', payment_id)
        
        await query.edit_message_text(
            f"✅ Платеж успешно зачислен!\n\n💰 Сумма: {amount}₽\n\nВаш баланс пополнен.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В меню", callback_data='back_main')]])
        )
    elif status == 'notpayed':
        await query.answer("⏳ Платеж еще не оплачен", show_alert=True)
    elif status == 'processing':
        await query.answer("⏳ Платеж обрабатывается", show_alert=True)
    else:
        await query.answer(f"❌ Статус: {status}", show_alert=True)

async def call_admin(query, context):
    """Вызов администратора с ограничением раз в 30 минут"""
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    current_time = datetime.now()
    
    # Проверяем cooldown (30 минут = 1800 секунд)
    if user_id in call_admin_cooldown:
        last_call = call_admin_cooldown[user_id]
        time_passed = (current_time - last_call).total_seconds()
        
        if time_passed < 1800:  # 30 минут
            remaining = int((1800 - time_passed) / 60)
            await query.answer(
                f"⏳ Вы уже вызывали админа. Попробуйте через {remaining} минут",
                show_alert=True
            )
            return
    
    # Обновляем время последнего вызова
    call_admin_cooldown[user_id] = current_time
    
    # Отправляем уведомление админу
    try:
        user_info = f"@{username}" if query.from_user.username else f"ID: {user_id}"
        admin_text = (
            f"📞 Вызов от пользователя!\n\n"
            f"👤 Пользователь: {user_info}\n"
            f"💬 Сообщение: Пользователь оплатил через Boosty и ждет выдачи ключа\n"
            f"⏰ Время: {current_time.strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Отправляем всем админам
        admins = await database.get_all_admins()
        admins.append(config.ADMIN_ID)  # Добавляем главного админа
        
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f'confirm_payment_{user_id}')],
            [InlineKeyboardButton("👤 Открыть профиль", callback_data=f'admin_user_{user_id}')]
        ]
        
        for admin_id in set(admins):  # set для удаления дубликатов
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
        
        await query.answer("✅ Администратор вызван! Ожидайте ответа", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка вызова админа: {e}")
        await query.answer("❌ Ошибка вызова администратора", show_alert=True)

async def show_support(query):
    text = f"❤️ Служба поддержки\n\nЕсли у вас есть вопросы, свяжитесь с нами:\n\n💬 Telegram: @{config.SUPPORT_USERNAME}"
    keyboard = [
        [InlineKeyboardButton(f"🔗 @{config.SUPPORT_USERNAME}", url=f'https://t.me/{config.SUPPORT_USERNAME}')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def get_trial(query):
    user_id = query.from_user.id
    
    if await database.has_trial(user_id):
        await query.edit_message_text("❌ Вы уже получали пробный ключ", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]]))
        return
    
    try:
        await query.edit_message_text("⏳ Создаю пробный ключ...")
        
        username = query.from_user.username or f"user{user_id}"
        sub_id = secrets.token_urlsafe(12)
        
        # Создаем для телефона (xhttp)
        result_phone = xui_client.create_client(email=f"{username}_trial_phone", days=3, traffic_gb=50, inbound_id=config.INBOUND_XHTTP, sub_id=sub_id)
        
        # Создаем для ПК (trojan) с тем же subId
        xui_client.create_client(email=f"{username}_trial_pc", days=3, traffic_gb=50, inbound_id=config.INBOUND_TROJAN, sub_id=sub_id)
        
        await database.add_subscription(
            user_id, 'trial', result_phone['client_id'], result_phone['config_link'], 
            result_phone['expires_at'], result_phone['email']
        )
        await database.mark_trial_used(user_id)
        
        text = f"🎁 Поздравляем!\n\nВот ваш пробный ключ на 3 дня:\n\n`{result_phone['config_link']}`\n\nАктивен до: {result_phone['expires_at'].strftime('%d.%m.%Y %H:%M')}\n\n📱 Включает оба протокола:\n• VLESS xhttp (для телефонов)\n• Trojan gRPC (для ПК)\n\n📱 Выберите ваше устройство:"
        
        keyboard = [
            [InlineKeyboardButton("📱 Android", callback_data='device_android')],
            [InlineKeyboardButton("🍎 iPhone", callback_data='device_iphone')],
            [InlineKeyboardButton("💻 Windows", callback_data='device_windows')],
            [InlineKeyboardButton("🍏 MacOS", callback_data='device_macos')],
            [InlineKeyboardButton("📺 Android TV", callback_data='device_tv')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Trial error: {e}")
        await query.edit_message_text(f"❌ Ошибка: {e}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]]))

async def show_promo(query):
    user_states[query.from_user.id] = 'waiting_promo'
    await query.edit_message_text("🎟 Введите промокод:\n\nЕсли у вас есть промокод, введите его ниже", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]]))

async def show_referral(query):
    user_id = query.from_user.id
    stats = await database.get_referral_stats(user_id)
    user = await database.get_user(user_id)
    
    # Получаем username бота из токена (он уже известен)
    bot_username = (await query.message.get_bot()).username
    
    ref_earned = user['ref_earned'] if user else 0
    
    text = (
        f"👥 Реферальная система\n\n"
        f"💰 Статистика:\n"
        f"👤 Приглашено: {stats['count']}\n"
        f"💵 Заработано: {ref_earned}₽\n\n"
        f"Ваша ссылка:\nhttps://t.me/{bot_username}?start={user_id}\n\n"
        f"🔥 Как это работает:\n"
        f"• Поделитесь ссылкой с друзьями\n"
        f"• Получайте 15% от их покупок\n"
        f"• Деньги начисляются на баланс автоматически"
    )
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]]))

async def show_device_instructions(query, device):
    instructions = {
        'android': "📱 Инструкция для Android:\n\n1️⃣ Скопируйте ключ (начинается с vless://)\n2️⃣ Установите Hiddify из Google Play\n3️⃣ Нажмите ➕ → «Импорт из буфера»\n4️⃣ Включите VPN и готово! ✅",
        'iphone': "🍎 Инструкция для iPhone:\n\n1️⃣ Скопируйте ключ\n2️⃣ Установите Streisand из App Store\n3️⃣ Нажмите ➕ → «Из буфера обмена»\n4️⃣ Готово! ✅",
        'windows': "💻 Инструкция для Windows:\n\n1️⃣ Скопируйте ключ\n2️⃣ Скачайте Hiddify\n3️⃣ Запустите от администратора\n4️⃣ Нажмите ➕ → «Из буфера»\n5️⃣ Готово! 🚀",
        'macos': "🍏 Инструкция для MacOS:\n\n1️⃣ Скопируйте ключ\n2️⃣ Установите Hiddify или V2Box\n3️⃣ Нажмите ➕ → Import from clipboard\n4️⃣ Готово! ✅",
        'tv': "📺 Инструкция для Android TV:\n\n1️⃣ Скачайте VPN4TV из Play Market\n2️⃣ Привяжите Telegram по инструкции\n3️⃣ Отправьте боту ваш ключ\n4️⃣ Включайте и пользуйтесь!"
    }
    
    await query.edit_message_text(instructions.get(device, "Инструкция недоступна"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='my_keys')]]))

async def process_purchase(query, plan_type):
    plan = config.PLANS.get(plan_type)
    if not plan:
        return
    
    user_id = query.from_user.id
    balance = await database.get_balance(user_id)
    
    if balance < plan['price']:
        await query.edit_message_text(f"❌ Недостаточно средств\n\nНужно: {plan['price']}₽\nВаш баланс: {balance}₽", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Пополнить", callback_data='balance')], [InlineKeyboardButton("⬅️ Назад", callback_data='buy')]]))
        return
    
    try:
        await query.edit_message_text("⏳ Создаю ключ...")
        
        username = query.from_user.username or f"user{user_id}"
        sub_id = secrets.token_urlsafe(12)
        
        result = xui_client.create_client(email=f"{username}_phone", days=plan['days'], traffic_gb=plan['traffic_gb'], inbound_id=config.INBOUND_XHTTP, sub_id=sub_id)
        xui_client.create_client(email=f"{username}_pc", days=plan['days'], traffic_gb=plan['traffic_gb'], inbound_id=config.INBOUND_TROJAN, sub_id=sub_id)
        
        await database.update_balance(user_id, -plan['price'])
        await database.add_subscription(
            user_id, plan_type, result['client_id'], result['config_link'], 
            result['expires_at'], result['email']
        )
        
        # Реферальная система - 15% рефереру
        referrer_id = await database.get_referrer(user_id)
        if referrer_id:
            ref_bonus = plan['price'] * 0.15
            await database.update_balance(referrer_id, ref_bonus)
            await database.add_referral_earning(referrer_id, ref_bonus)
        
        text = f"✅ Ключ создан!\n\n📅 Тариф: {plan['name']}\n⏰ До: {result['expires_at'].strftime('%d.%m.%Y')}\n\n🔑 Ссылка:\n`{result['config_link']}`\n\n📱 Выберите устройство:"
        
        keyboard = [
            [InlineKeyboardButton("📱 Android", callback_data='device_android')],
            [InlineKeyboardButton("🍎 iPhone", callback_data='device_iphone')],
            [InlineKeyboardButton("💻 Windows", callback_data='device_windows')],
            [InlineKeyboardButton("🍏 MacOS", callback_data='device_macos')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='back_main')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Purchase error: {e}")
        await query.edit_message_text(f"❌ Ошибка: {e}")

# ===== ADMIN PANEL =====

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await database.is_admin(update.effective_user.id):
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 Пользователи", callback_data='admin_users')],
        [InlineKeyboardButton("🎟 Промокоды", callback_data='admin_promos')],
        [InlineKeyboardButton("👑 Админы", callback_data='admin_admins')],
        [InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("🗑 Очистить истекшие", callback_data='admin_cleanup')]
    ]
    
    await update.message.reply_text("🔧 Админ панель:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_admin_menu(query):
    if not await database.is_admin(query.from_user.id):
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 Пользователи", callback_data='admin_users')],
        [InlineKeyboardButton("🎟 Промокоды", callback_data='admin_promos')],
        [InlineKeyboardButton("👑 Админы", callback_data='admin_admins')],
        [InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("🗑 Очистить истекшие", callback_data='admin_cleanup')],
        [InlineKeyboardButton("⬅️ Вернуться в меню", callback_data='back_main')]
    ]
    
    await query.edit_message_text("🔧 Админ панель:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_users(query):
    if not await database.is_admin(query.from_user.id):
        return
    
    users = await database.get_all_users()
    keyboard = []
    for u in users[:20]:
        name = u['username'] or str(u['user_id'])
        keyboard.append([InlineKeyboardButton(f"👤 {name} | {u['balance']}₽", callback_data=f'admin_user_{u["user_id"]}')])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='admin')])
    
    await query.edit_message_text(f"👥 Пользователи ({len(users)}):", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_user_details(query, user_id):
    if not await database.is_admin(query.from_user.id):
        return
    
    user = await database.get_user(user_id)
    if not user:
        await query.edit_message_text("Пользователь не найден", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='admin_users')]]))
        return
    
    # Конвертируем sqlite3.Row в dict
    user_dict = dict(user)
    
    banned = user_dict.get('banned', False)
    trial_used = user_dict.get('trial_used', False)
    
    banned_status = "🔴 Забанен" if banned else "🟢 Активен"
    trial_status = "использован" if trial_used else "доступен"
    
    text = f"👤 {user_dict.get('username') or user_id}\n\n💰 Баланс: {user_dict.get('balance', 0)}₽\n🎁 Триал: {trial_status}\nСтатус: {banned_status}"
    
    keyboard = [
        [InlineKeyboardButton("💰 Изменить баланс", callback_data=f'admin_set_balance_{user_id}')],
        [InlineKeyboardButton("🔄 Сбросить триал", callback_data=f'admin_reset_trial_{user_id}')],
        [InlineKeyboardButton("🔑 Ключи пользователя", callback_data=f'admin_user_keys_{user_id}')],
    ]
    
    if banned:
        keyboard.append([InlineKeyboardButton("✅ Разбанить", callback_data=f'admin_unban_{user_id}')])
    else:
        keyboard.append([InlineKeyboardButton("🔴 Забанить", callback_data=f'admin_ban_{user_id}')])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='admin_users')])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_reset_trial(query, user_id):
    if not await database.is_admin(query.from_user.id):
        return
    
    await database.reset_trial(user_id)
    await query.edit_message_text(f"✅ Триал сброшен для {user_id}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_user_{user_id}')]]))

async def admin_set_balance_start(query, user_id):
    if not await database.is_admin(query.from_user.id):
        return
    
    user_states[query.from_user.id] = f'admin_balance_{user_id}'
    await query.edit_message_text(f"Введите новый баланс для пользователя {user_id}:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Отмена", callback_data=f'admin_user_{user_id}')]]))

async def admin_promos(query):
    if not await database.is_admin(query.from_user.id):
        return
    
    promos = await database.get_all_promos()
    text = "🎟 Промокоды:\n\n"
    keyboard = []
    
    for p in promos:
        text += f"• {p['code']} - {p['bonus']}₽ ({p['uses']}/{p['max_uses']})\n"
        keyboard.append([InlineKeyboardButton(f"❌ {p['code']}", callback_data=f'admin_del_promo_{p["code"]}')])
    
    if not promos:
        text += "Нет промокодов"
    
    keyboard.append([InlineKeyboardButton("➕ Добавить промокод", callback_data='admin_add_promo')])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='admin')])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_add_promo_start(query):
    if not await database.is_admin(query.from_user.id):
        return
    
    user_states[query.from_user.id] = 'admin_add_promo'
    await query.edit_message_text("Введите промокод в формате:\nКОД СУММА КОЛИЧЕСТВО\n\nПример: BONUS100 100 50", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Отмена", callback_data='admin_promos')]]))

async def admin_delete_promo(query, code):
    if not await database.is_admin(query.from_user.id):
        return
    
    await database.delete_promo(code)
    await admin_promos(query)

async def admin_stats_menu(query):
    if not await database.is_admin(query.from_user.id):
        return
    
    stats = await database.get_admin_stats()
    text = f"📊 Статистика:\n\n👥 Пользователей: {stats['users']}\n🔑 Активных ключей: {stats['active_keys']}\n💰 Платежей: {stats['total_payments']}₽"
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='admin')]]))

async def admin_admins_list(query):
    if query.from_user.id != config.ADMIN_ID:
        await query.answer("Только владелец может управлять админами")
        return
    
    admins = await database.get_all_admins()
    text = f"👑 Админы ({len(admins)}):\n\n"
    keyboard = []
    
    for admin_id in admins:
        user = await database.get_user(admin_id)
        name = user['username'] if user else str(admin_id)
        text += f"• {name} ({admin_id})\n"
        keyboard.append([InlineKeyboardButton(f"❌ {name}", callback_data=f'admin_remove_admin_{admin_id}')])
    
    keyboard.append([InlineKeyboardButton("➕ Добавить админа", callback_data='admin_add_admin_')])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='admin')])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_add_admin_start(query):
    if query.from_user.id != config.ADMIN_ID:
        return
    
    user_states[query.from_user.id] = 'admin_add_admin'
    await query.edit_message_text("Введите ID пользователя для назначения админом:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Отмена", callback_data='admin_admins')]]))

async def admin_remove_admin(query, admin_id):
    if query.from_user.id != config.ADMIN_ID:
        return
    
    await database.remove_admin(admin_id)
    await admin_admins_list(query)

async def admin_ban_user(query, user_id):
    if not await database.is_admin(query.from_user.id):
        return
    
    await database.ban_user(user_id)
    await query.edit_message_text(f"✅ Пользователь {user_id} забанен", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_user_{user_id}')]]))

async def admin_unban_user(query, user_id):
    if not await database.is_admin(query.from_user.id):
        return
    
    await database.unban_user(user_id)
    await query.edit_message_text(f"✅ Пользователь {user_id} разбанен", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_user_{user_id}')]]))

async def admin_user_keys(query, user_id):
    if not await database.is_admin(query.from_user.id):
        return
    
    subs = await database.get_user_subscriptions(user_id)
    
    if not subs:
        await query.edit_message_text("У пользователя нет ключей", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_user_{user_id}')]]))
        return
    
    text = f"🔑 Ключи пользователя {user_id}:\n\n"
    keyboard = []
    
    for sub in subs:
        plan_name = config.PLANS.get(sub['plan_type'], {}).get('name', sub['plan_type'])
        expires = datetime.fromisoformat(sub['expires_at'])
        text += f"• {plan_name} до {expires.strftime('%d.%m.%Y')}\n"
        keyboard.append([InlineKeyboardButton(f"❌ Удалить {plan_name}", callback_data=f'admin_del_key_{sub["id"]}')])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_user_{user_id}')])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_delete_key(query, sub_id):
    if not await database.is_admin(query.from_user.id):
        return
    
    sub = await database.get_subscription_by_id(sub_id)
    if not sub:
        await query.edit_message_text("Ключ не найден")
        return
    
    await database.delete_subscription(sub_id)
    await query.edit_message_text(f"✅ Ключ удален", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_user_keys_{sub["user_id"]}')]]))

async def admin_confirm_payment(query, user_id):
    """Подтверждение оплаты через Boosty - выбор тарифа"""
    if not await database.is_admin(query.from_user.id):
        return
    
    user = await database.get_user(user_id)
    if not user:
        await query.edit_message_text("❌ Пользователь не найден")
        return
    
    username = user['username'] or f"ID: {user_id}"
    
    text = f"💳 Подтверждение оплаты для {username}\n\nВыберите тариф:"
    
    keyboard = [
        [InlineKeyboardButton("📅 1 месяц (100₽)", callback_data=f'boosty_plan_{user_id}_1_month')],
        [InlineKeyboardButton("📅 3 месяца (400₽)", callback_data=f'boosty_plan_{user_id}_3_months')],
        [InlineKeyboardButton("📅 6 месяцев (700₽)", callback_data=f'boosty_plan_{user_id}_6_months')],
        [InlineKeyboardButton("❌ Отмена", callback_data='admin')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_process_boosty_payment(query, user_id, plan_id, context):
    """Обработка подтверждения оплаты - пополнение баланса"""
    if not await database.is_admin(query.from_user.id):
        return
    
    plan = config.PLANS.get(plan_id)
    if not plan:
        await query.edit_message_text("❌ Тариф не найден")
        return
    
    try:
        # Пополняем баланс пользователю
        await database.update_balance(user_id, plan['price'])
        
        user = await database.get_user(user_id)
        username = user['username'] or f"ID: {user_id}"
        
        # Уведомляем админа
        await query.edit_message_text(
            f"✅ Баланс пополнен!\n\n"
            f"👤 Пользователь: {username}\n"
            f"💰 Сумма: {plan['price']}₽\n"
            f"📅 Тариф: {plan['name']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В админ панель", callback_data='admin')]])
        )
        
        # Отправляем уведомление пользователю
        try:
            notification_text = (
                f"✅ Ваш баланс пополнен!\n\n"
                f"💰 Сумма: {plan['price']}₽\n"
                f"📅 Тариф: {plan['name']}\n\n"
                f"Теперь вы можете купить подписку в главном меню!"
            )
            
            keyboard = [[InlineKeyboardButton("🛍 Купить подписку", callback_data='buy')]]
            
            await context.bot.send_message(
                chat_id=user_id,
                text=notification_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка пополнения баланса: {e}")
        await query.edit_message_text(f"❌ Ошибка: {e}")

async def admin_manual_cleanup(query):
    """Ручной запуск очистки истекших подписок"""
    if not await database.is_admin(query.from_user.id):
        return
    
    await query.edit_message_text("⏳ Запускаю очистку истекших подписок...")
    
    try:
        # Получаем ВСЕ активные подписки для проверки
        all_subs = await database.get_all_active_subscriptions()
        
        if not all_subs:
            await query.edit_message_text(
                "✅ Активных подписок не найдено",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='admin')]])
            )
            return
        
        deleted_count = 0
        failed_count = 0
        expired_by_date = 0
        expired_in_panel = 0
        
        for sub in all_subs:
            try:
                email = sub['email'] if 'email' in sub.keys() and sub['email'] else None
                xui_client_id = sub['xui_client_id'] if 'xui_client_id' in sub.keys() and sub['xui_client_id'] else None
                sub_id = sub['id']
                expires_at = datetime.fromisoformat(sub['expires_at'])
                
                # Проверка 1: Истек срок по дате
                is_expired_by_date = expires_at <= datetime.now()
                
                # Проверка 2: Проверяем в панели
                is_expired_in_xui = False
                
                if email and not is_expired_by_date:
                    try:
                        loop = asyncio.get_event_loop()
                        for inbound_id in [config.INBOUND_XHTTP, config.INBOUND_TROJAN]:
                            try:
                                inbound_info = await loop.run_in_executor(
                                    None,
                                    xui_client.get_inbound_info,
                                    inbound_id
                                )
                                
                                if inbound_info:
                                    settings = json.loads(inbound_info.get('settings', '{}'))
                                    clients = settings.get('clients', [])
                                    
                                    for client in clients:
                                        client_email = client.get('email', '')
                                        if email in client_email or client_email.startswith(email.split('_')[0]):
                                            expiry_time = client.get('expiryTime', 0)
                                            
                                            if expiry_time > 0 and expiry_time < datetime.now().timestamp() * 1000:
                                                is_expired_in_xui = True
                                                break
                                    
                                    if is_expired_in_xui:
                                        break
                            except:
                                pass
                    except:
                        pass
                
                # Если истекла - удаляем
                if is_expired_by_date or is_expired_in_xui:
                    if is_expired_by_date:
                        expired_by_date += 1
                    if is_expired_in_xui:
                        expired_in_panel += 1
                    
                    client_deleted = False
                    
                    # Удаление по email
                    if email:
                        emails_to_delete = []
                        
                        if '_trial_phone' in email:
                            base = email.replace('_trial_phone', '')
                            emails_to_delete = [f"{base}_trial_phone", f"{base}_trial_pc"]
                        elif '_trial_pc' in email:
                            base = email.replace('_trial_pc', '')
                            emails_to_delete = [f"{base}_trial_phone", f"{base}_trial_pc"]
                        elif '_phone' in email:
                            base = email.replace('_phone', '')
                            emails_to_delete = [f"{base}_phone", f"{base}_pc"]
                        elif '_pc' in email:
                            base = email.replace('_pc', '')
                            emails_to_delete = [f"{base}_phone", f"{base}_pc"]
                        else:
                            emails_to_delete = [email]
                        
                        for email_to_delete in emails_to_delete:
                            try:
                                loop = asyncio.get_event_loop()
                                result = await loop.run_in_executor(
                                    None, 
                                    xui_client.delete_client_by_email, 
                                    email_to_delete,
                                    None
                                )
                                if result:
                                    client_deleted = True
                            except:
                                pass
                    
                    # Удаление по UUID
                    if not client_deleted and xui_client_id:
                        try:
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(
                                None, 
                                xui_client.delete_client_by_uuid, 
                                xui_client_id,
                                None
                            )
                            if result:
                                client_deleted = True
                        except:
                            pass
                    
                    # Деактивируем в БД
                    await database.deactivate_subscription(sub_id)
                    
                    if client_deleted:
                        deleted_count += 1
                    else:
                        failed_count += 1
                    
            except:
                failed_count += 1
                try:
                    await database.deactivate_subscription(sub['id'])
                except:
                    pass
                continue
        
        text = (
            f"📊 Очистка завершена!\n\n"
            f"✅ Удалено из панели: {deleted_count}\n"
            f"⚠️ Не найдено в панели: {failed_count}\n"
            f"📋 Всего проверено: {len(all_subs)}\n\n"
            f"Причины истечения:\n"
            f"📅 По дате в БД: {expired_by_date}\n"
            f"⏰ По сроку в панели: {expired_in_panel}"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='admin')]])
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка при очистке: {e}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='admin')]])
        )

# ===== MESSAGE HANDLER =====

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id)
    
    if state == 'waiting_promo':
        user_states.pop(user_id, None)
        promo = await database.check_promo(text)
        if promo:
            await database.use_promo(user_id, text)
            await database.update_balance(user_id, promo['bonus'])
            await update.message.reply_text(f"✅ Промокод активирован!\n+{promo['bonus']}₽", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В меню", callback_data='back_main')]]))
        else:
            await update.message.reply_text("❌ Промокод не найден", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ В меню", callback_data='back_main')]]))
    
    elif state and state.startswith('admin_balance_'):
        if not await database.is_admin(user_id):
            return
        target_id = int(state.replace('admin_balance_', ''))
        user_states.pop(user_id, None)
        try:
            amount = float(text)
            await database.set_balance(target_id, amount)
            await update.message.reply_text(f"✅ Баланс установлен: {amount}₽", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_user_{target_id}')]]))
        except:
            await update.message.reply_text("❌ Неверный формат")
    
    elif state == 'admin_add_promo':
        if not await database.is_admin(user_id):
            return
        user_states.pop(user_id, None)
        try:
            parts = text.split()
            code, bonus, max_uses = parts[0], float(parts[1]), int(parts[2]) if len(parts) > 2 else 100
            await database.create_promo(code, bonus, max_uses)
            await update.message.reply_text(f"✅ Промокод {code} создан!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ К промокодам", callback_data='admin_promos')]]))
        except:
            await update.message.reply_text("❌ Неверный формат. Пример: BONUS100 100 50")
    
    elif state == 'admin_add_admin':
        if user_id != config.ADMIN_ID:
            return
        user_states.pop(user_id, None)
        try:
            new_admin_id = int(text)
            await database.add_admin(new_admin_id)
            await update.message.reply_text(f"✅ Пользователь {new_admin_id} назначен админом", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ К админам", callback_data='admin_admins')]]))
        except:
            await update.message.reply_text("❌ Неверный ID")

# ===== AUTO CLEANUP EXPIRED SUBSCRIPTIONS =====

async def cleanup_expired_subscriptions():
    """Автоматическая очистка истекших подписок из панели"""
    # Первая проверка через 30 секунд после запуска
    await asyncio.sleep(30)
    
    while True:
        try:
            logger.info("🔍 Проверка истекших подписок...")
            
            # Получаем ВСЕ активные подписки для проверки в панели
            all_subs = await database.get_all_active_subscriptions()
            
            logger.info(f"📋 Получено подписок из БД: {len(all_subs) if all_subs else 0}")
            
            deleted_count = 0
            failed_count = 0
            expired_by_date = 0
            expired_in_panel = 0
            
            # ЧАСТЬ 1: Проверяем подписки из БД
            if all_subs:
                logger.info(f"📋 Проверяю {len(all_subs)} активных подписок из БД...")
                
                for sub in all_subs:
                    try:
                        email = sub['email'] if 'email' in sub.keys() and sub['email'] else None
                        xui_client_id = sub['xui_client_id'] if 'xui_client_id' in sub.keys() and sub['xui_client_id'] else None
                        sub_id = sub['id']
                        user_id = sub['user_id']
                        expires_at = datetime.fromisoformat(sub['expires_at'])
                        
                        logger.info(f"Проверка подписки #{sub_id}: email={email}, expires={expires_at}")
                        
                        # Проверка 1: Истек срок по дате в БД
                        is_expired_by_date = expires_at <= datetime.now()
                        
                        # Проверка 2: Проверяем статус в панели (expiryTime)
                        is_expired_in_xui = False
                        
                        if email and not is_expired_by_date:
                            # Проверяем клиента в панели только если в БД еще не истек
                            try:
                                loop = asyncio.get_event_loop()
                                for inbound_id in [config.INBOUND_XHTTP, config.INBOUND_TROJAN]:
                                    try:
                                        inbound_info = await loop.run_in_executor(
                                            None,
                                            xui_client.get_inbound_info,
                                            inbound_id
                                        )
                                        
                                        if inbound_info:
                                            settings = json.loads(inbound_info.get('settings', '{}'))
                                            clients = settings.get('clients', [])
                                            
                                            for client in clients:
                                                client_email = client.get('email', '')
                                                if email in client_email or client_email.startswith(email.split('_')[0]):
                                                    expiry_time = client.get('expiryTime', 0)
                                                    
                                                    # Проверяем истек ли срок в панели
                                                    if expiry_time > 0 and expiry_time < datetime.now().timestamp() * 1000:
                                                        is_expired_in_xui = True
                                                        logger.info(f"Клиент {client_email} истек в панели (expiryTime: {expiry_time})")
                                                        break
                                            
                                            if is_expired_in_xui:
                                                break
                                    except Exception as e:
                                        logger.debug(f"Ошибка проверки inbound {inbound_id}: {e}")
                            except Exception as e:
                                logger.debug(f"Не удалось проверить клиента в панели: {e}")
                        
                        # Удаляем если истекла по дате ИЛИ в панели
                        if is_expired_by_date or is_expired_in_xui:
                            if is_expired_by_date:
                                expired_by_date += 1
                                logger.info(f"Подписка #{sub_id} истекла по дате: {expires_at}")
                            if is_expired_in_xui:
                                expired_in_panel += 1
                                logger.info(f"Подписка #{sub_id} истекла в панели")
                            
                            client_deleted = False
                            
                            # Удаление по email
                            if email:
                                emails_to_delete = []
                                
                                if '_trial_phone' in email:
                                    base = email.replace('_trial_phone', '')
                                    emails_to_delete = [f"{base}_trial_phone", f"{base}_trial_pc"]
                                elif '_trial_pc' in email:
                                    base = email.replace('_trial_pc', '')
                                    emails_to_delete = [f"{base}_trial_phone", f"{base}_trial_pc"]
                                elif '_phone' in email:
                                    base = email.replace('_phone', '')
                                    emails_to_delete = [f"{base}_phone", f"{base}_pc"]
                                elif '_pc' in email:
                                    base = email.replace('_pc', '')
                                    emails_to_delete = [f"{base}_phone", f"{base}_pc"]
                                else:
                                    emails_to_delete = [email]
                                
                                for email_to_delete in emails_to_delete:
                                    try:
                                        loop = asyncio.get_event_loop()
                                        result = await loop.run_in_executor(
                                            None, 
                                            xui_client.delete_client_by_email, 
                                            email_to_delete,
                                            None
                                        )
                                        if result:
                                            client_deleted = True
                                            logger.info(f"✅ Удален клиент: {email_to_delete}")
                                    except Exception as e:
                                        logger.debug(f"Клиент {email_to_delete} не найден: {e}")
                            
                            # Удаление по UUID
                            if not client_deleted and xui_client_id:
                                try:
                                    loop = asyncio.get_event_loop()
                                    result = await loop.run_in_executor(
                                        None, 
                                        xui_client.delete_client_by_uuid, 
                                        xui_client_id,
                                        None
                                    )
                                    if result:
                                        client_deleted = True
                                        logger.info(f"✅ Удален клиент по UUID: {xui_client_id}")
                                except Exception as e:
                                    logger.debug(f"Клиент с UUID {xui_client_id} не найден: {e}")
                            
                            # Деактивируем в БД
                            await database.deactivate_subscription(sub_id)
                            
                            if client_deleted:
                                deleted_count += 1
                                logger.info(f"✅ Подписка #{sub_id} успешно удалена")
                            else:
                                failed_count += 1
                                logger.warning(f"⚠️ Подписка #{sub_id} деактивирована в БД, но не найдена в панели")
                            
                    except Exception as e:
                        failed_count += 1
                        sub_id_error = sub.get('id', 'unknown')
                        logger.error(f"❌ Ошибка при обработке подписки #{sub_id_error}: {e}")
                        try:
                            await database.deactivate_subscription(sub['id'])
                        except:
                            pass
                        continue
            
            # ЧАСТЬ 2: Проверяем панель напрямую (на случай если в БД нет подписок)
            logger.info("📋 Проверка панели напрямую...")
            loop = asyncio.get_event_loop()
            
            for inbound_id in [config.INBOUND_XHTTP, config.INBOUND_TROJAN]:
                try:
                    inbound_info = await loop.run_in_executor(
                        None,
                        xui_client.get_inbound_info,
                        inbound_id
                    )
                    
                    if inbound_info:
                        settings = json.loads(inbound_info.get('settings', '{}'))
                        clients = settings.get('clients', [])
                        protocol = inbound_info.get('protocol', 'unknown')
                        
                        logger.info(f"Inbound #{inbound_id} ({protocol}): {len(clients)} клиентов")
                        
                        for client in clients:
                            email = client.get('email', '')
                            expiry_time = client.get('expiryTime', 0)
                            
                            # Проверяем истек ли срок
                            if expiry_time > 0 and expiry_time < datetime.now().timestamp() * 1000:
                                logger.info(f"Найден истекший клиент в панели: {email}")
                                
                                try:
                                    if protocol == 'trojan':
                                        client_id = client.get('password')
                                    else:
                                        client_id = client.get('id')
                                    
                                    if client_id:
                                        result = await loop.run_in_executor(
                                            None,
                                            xui_client.delete_client,
                                            inbound_id,
                                            client_id
                                        )
                                        if result:
                                            deleted_count += 1
                                            expired_in_panel += 1
                                            logger.info(f"✅ Удален клиент из панели: {email}")
                                except Exception as e:
                                    logger.error(f"Ошибка удаления {email}: {e}")
                
                except Exception as e:
                    logger.error(f"Ошибка проверки inbound #{inbound_id}: {e}")
            
            if deleted_count > 0 or failed_count > 0:
                logger.info(f"📊 Итого: удалено {deleted_count}, не найдено {failed_count}")
                logger.info(f"📊 Причины: по дате {expired_by_date}, в панели {expired_in_panel}")
            else:
                logger.info("✅ Истекших подписок не найдено")
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в cleanup_expired_subscriptions: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Ждем 1 час до следующей проверки (3600 секунд)
        await asyncio.sleep(3600)

# ===== SUBSCRIPTION EXPIRY NOTIFICATIONS =====

async def check_expiring_subscriptions(context):
    """Проверка подписок, которые скоро истекут (за 4, 3, 2, 1 день)"""
    while True:
        try:
            await asyncio.sleep(3600)  # Проверяем каждый час
            
            logger.info("🔔 Проверка истекающих подписок...")
            
            all_subs = await database.get_all_active_subscriptions()
            
            if not all_subs:
                continue
            
            current_time = datetime.now()
            
            for sub in all_subs:
                try:
                    user_id = sub['user_id']
                    expires_at = datetime.fromisoformat(sub['expires_at'])
                    plan_type = sub['plan_type']
                    
                    # Вычисляем сколько дней осталось
                    time_left = expires_at - current_time
                    days_left = time_left.days
                    hours_left = time_left.seconds // 3600
                    
                    # Отправляем уведомления за 4, 3, 2, 1 день
                    if days_left in [4, 3, 2, 1] and hours_left < 2:
                        # Генерируем разные сообщения
                        messages = {
                            4: [
                                f"⏰ Напоминание!\n\nВаша подписка истекает через 4 дня.\n\nНе забудьте продлить, чтобы не потерять доступ!",
                                f"🔔 Внимание!\n\nДо окончания вашей подписки осталось 4 дня.\n\nРекомендуем продлить заранее!",
                                f"⚠️ Уведомление\n\nВаша подписка закончится через 4 дня.\n\nПродлите сейчас и получите бонус!"
                            ],
                            3: [
                                f"⏰ Осталось 3 дня!\n\nВаша подписка скоро истечет.\n\nПродлите прямо сейчас!",
                                f"🔔 Важно!\n\nДо конца подписки 3 дня.\n\nНе упустите момент!",
                                f"⚠️ Напоминание\n\nВсего 3 дня до окончания подписки.\n\nПродлите, чтобы не потерять доступ!"
                            ],
                            2: [
                                f"⏰ Осталось 2 дня!\n\nВаша подписка заканчивается послезавтра.\n\nПродлите сейчас!",
                                f"🔔 Срочно!\n\nДо конца подписки 2 дня.\n\nУспейте продлить!",
                                f"⚠️ Внимание!\n\nПодписка истекает через 2 дня.\n\nНе теряйте доступ!"
                            ],
                            1: [
                                f"⏰ ПОСЛЕДНИЙ ДЕНЬ!\n\nВаша подписка истекает завтра.\n\nПродлите СРОЧНО!",
                                f"🔔 ВАЖНО!\n\nОстался 1 день до окончания подписки.\n\nПродлите прямо сейчас!",
                                f"⚠️ СРОЧНО!\n\nПодписка заканчивается завтра.\n\nНе упустите!"
                            ]
                        }
                        
                        import random
                        message = random.choice(messages[days_left])
                        
                        keyboard = [
                            [InlineKeyboardButton("🔄 Продлить подписку", callback_data='buy')],
                            [InlineKeyboardButton("💰 Пополнить баланс", callback_data='balance')]
                        ]
                        
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=message,
                                reply_markup=InlineKeyboardMarkup(keyboard)
                            )
                            logger.info(f"Отправлено уведомление пользователю {user_id} (осталось {days_left} дней)")
                        except Exception as e:
                            logger.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                
                except Exception as e:
                    logger.error(f"Ошибка обработки подписки: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Ошибка в check_expiring_subscriptions: {e}")
            import traceback
            logger.error(traceback.format_exc())

# ===== MAIN =====

async def main_async():
    await database.init_db()
    
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Бот запущен!")
    
    # Запускаем фоновую задачу для автоматической очистки истекших подписок
    asyncio.create_task(cleanup_expired_subscriptions())
    logger.info("Запущена автоматическая очистка истекших подписок")
    
    # Запускаем фоновую задачу для уведомлений об истечении подписок
    asyncio.create_task(check_expiring_subscriptions(app))
    logger.info("Запущена система уведомлений об истечении подписок")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹ Остановка бота...")
    finally:
        logger.info("🛑 Завершение работы...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("✅ Бот остановлен")

if __name__ == '__main__':
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        # Игнорируем KeyboardInterrupt при завершении
        pass
