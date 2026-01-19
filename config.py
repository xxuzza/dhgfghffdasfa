import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")

ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
if ADMIN_ID == 0:
    print("⚠️ ADMIN_ID не установлен в .env файле")

# 3X-UI Panel
XUI_PANEL_URL = os.getenv('XUI_PANEL_URL')
XUI_USERNAME = os.getenv('XUI_USERNAME')
XUI_PASSWORD = os.getenv('XUI_PASSWORD')
XUI_INBOUND_ID = int(os.getenv('XUI_INBOUND_ID', 1))

if not XUI_PANEL_URL or not XUI_USERNAME or not XUI_PASSWORD:
    raise ValueError("❌ Настройки 3X-UI (XUI_PANEL_URL, XUI_USERNAME, XUI_PASSWORD) не найдены в .env файле!")

# Payment
PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN')

# CrystalPay
CRYSTALPAY_NAME = os.getenv('CRYSTALPAY_NAME')
CRYSTALPAY_SECRET1 = os.getenv('CRYSTALPAY_SECRET1')
CRYSTALPAY_SECRET2 = os.getenv('CRYSTALPAY_SECRET2')

# Support
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME', 'your_support')

# Subscription Plans
PLANS = {
    '1_month': {'name': '1 месяц', 'days': 30, 'price': 100, 'traffic_gb': 200, 'stars': 100},
    '3_months': {'name': '3 месяца', 'days': 90, 'price': 400, 'traffic_gb': 600, 'stars': 200},
    '6_months': {'name': '6 месяцев', 'days': 180, 'price': 700, 'traffic_gb': 1200, 'stars': 400},
}

# Inbound IDs для разных протоколов
INBOUND_XHTTP = 3  # VLESS xhttp - для телефонов
INBOUND_TROJAN = 4  # Trojan gRPC - для ПК

# Subscription URL path (из настроек панели)
SUB_PATH = 'Gl5YqOBPNE'

# Database
DB_PATH = 'vpn_bot.db'
