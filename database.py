import aiosqlite
import config
from datetime import datetime

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0,
                referrer_id INTEGER,
                ref_earned REAL DEFAULT 0,
                trial_used BOOLEAN DEFAULT 0,
                banned BOOLEAN DEFAULT 0,
                agreed_policy BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_type TEXT,
                xui_client_id TEXT,
                email TEXT,
                config_link TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Добавляем колонку email если её нет (миграция для существующих БД)
        try:
            await db.execute('ALTER TABLE subscriptions ADD COLUMN email TEXT')
        except:
            pass  # Колонка уже существует
        await db.commit()
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                plan_type TEXT,
                status TEXT,
                payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                bonus REAL,
                max_uses INTEGER DEFAULT 1,
                uses INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS promo_uses (
                user_id INTEGER,
                code TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, code)
            )
        ''')
        
        await db.commit()

async def add_user(user_id, username):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
            (user_id, username)
        )
        await db.commit()

async def has_agreed_policy(user_id):
    """Проверить согласие с политикой"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute('SELECT agreed_policy FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else False

async def set_agreed_policy(user_id):
    """Установить согласие с политикой"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('UPDATE users SET agreed_policy = 1 WHERE user_id = ?', (user_id,))
        await db.commit()

async def get_balance(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def update_balance(user_id, amount):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            'UPDATE users SET balance = balance + ? WHERE user_id = ?',
            (amount, user_id)
        )
        await db.commit()

async def set_referrer(user_id, referrer_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            'UPDATE users SET referrer_id = ? WHERE user_id = ? AND referrer_id IS NULL',
            (referrer_id, user_id)
        )
        await db.commit()

async def get_referral_stats(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute(
            'SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,)
        ) as cursor:
            count = (await cursor.fetchone())[0]
        
        # Здесь можно добавить подсчет заработка
        return {'count': count, 'earned': 0}

async def has_trial(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute(
            'SELECT trial_used FROM users WHERE user_id = ?', (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else False

async def mark_trial_used(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            'UPDATE users SET trial_used = 1 WHERE user_id = ?', (user_id,)
        )
        await db.commit()

async def add_subscription(user_id, plan_type, xui_client_id, config_link, expires_at, email=None):
    async with aiosqlite.connect(config.DB_PATH) as db:
        # Конвертируем datetime в строку для SQLite
        if isinstance(expires_at, datetime):
            expires_at_str = expires_at.isoformat()
        else:
            expires_at_str = str(expires_at)
        
        await db.execute(
            '''INSERT INTO subscriptions 
               (user_id, plan_type, xui_client_id, config_link, expires_at, email) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, plan_type, xui_client_id, config_link, expires_at_str, email)
        )
        await db.commit()

async def get_active_subscription(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            '''SELECT * FROM subscriptions 
               WHERE user_id = ? AND is_active = 1 AND expires_at > datetime('now')
               ORDER BY created_at DESC LIMIT 1''',
            (user_id,)
        ) as cursor:
            return await cursor.fetchone()

async def get_user_subscriptions(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            '''SELECT * FROM subscriptions 
               WHERE user_id = ? AND is_active = 1 AND expires_at > datetime('now')
               ORDER BY created_at DESC''',
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

async def check_promo(code):
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            'SELECT * FROM promo_codes WHERE code = ? AND is_active = 1 AND uses < max_uses',
            (code,)
        ) as cursor:
            return await cursor.fetchone()

async def use_promo(user_id, code):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO promo_uses (user_id, code) VALUES (?, ?)',
            (user_id, code)
        )
        await db.execute(
            'UPDATE promo_codes SET uses = uses + 1 WHERE code = ?',
            (code,)
        )
        await db.commit()

async def add_payment(user_id, amount, plan_type, status, payment_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            '''INSERT INTO payments 
               (user_id, amount, plan_type, status, payment_id) 
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, amount, plan_type, status, payment_id)
        )
        await db.commit()

async def get_admin_stats():
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            users = (await cursor.fetchone())[0]
        
        async with db.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE is_active = 1 AND expires_at > datetime('now')"
        ) as cursor:
            active_keys = (await cursor.fetchone())[0]
        
        async with db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'completed'"
        ) as cursor:
            total_payments = (await cursor.fetchone())[0]
        
        return {
            'users': users,
            'active_keys': active_keys,
            'total_payments': total_payments
        }

async def delete_subscription_db(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            'UPDATE subscriptions SET is_active = 0 WHERE user_id = ?',
            (user_id,)
        )
        await db.commit()


# ===== ADMIN FUNCTIONS =====

async def reset_trial(user_id):
    """Сбросить пробный период"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('UPDATE users SET trial_used = 0 WHERE user_id = ?', (user_id,))
        await db.commit()

async def set_balance(user_id, amount):
    """Установить баланс"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('UPDATE users SET balance = ? WHERE user_id = ?', (amount, user_id))
        await db.commit()

async def get_all_users():
    """Получить всех пользователей"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT 50') as cursor:
            return await cursor.fetchall()

async def get_user(user_id):
    """Получить пользователя"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def create_promo(code, bonus, max_uses=100):
    """Создать промокод"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO promo_codes (code, bonus, max_uses, uses, is_active) VALUES (?, ?, ?, 0, 1)',
            (code, bonus, max_uses)
        )
        await db.commit()

async def delete_promo(code):
    """Удалить промокод"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('DELETE FROM promo_codes WHERE code = ?', (code,))
        await db.commit()

async def get_all_promos():
    """Получить все промокоды"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM promo_codes') as cursor:
            return await cursor.fetchall()


async def add_admin(user_id):
    """Добавить админа"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)')
        await db.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (user_id,))
        await db.commit()

async def remove_admin(user_id):
    """Удалить админа"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        await db.commit()

async def is_admin(user_id):
    """Проверить админа"""
    if user_id == config.ADMIN_ID:
        return True
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)')
        async with db.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone() is not None

async def get_all_admins():
    """Получить всех админов"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)')
        async with db.execute('SELECT user_id FROM admins') as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def ban_user(user_id):
    """Забанить пользователя"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('UPDATE users SET banned = 1 WHERE user_id = ?', (user_id,))
        await db.commit()

async def unban_user(user_id):
    """Разбанить пользователя"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('UPDATE users SET banned = 0 WHERE user_id = ?', (user_id,))
        await db.commit()

async def is_banned(user_id):
    """Проверить бан"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else False

async def delete_subscription(sub_id):
    """Удалить подписку"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('UPDATE subscriptions SET is_active = 0 WHERE id = ?', (sub_id,))
        await db.commit()

async def get_subscription_by_id(sub_id):
    """Получить подписку по ID"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM subscriptions WHERE id = ?', (sub_id,)) as cursor:
            return await cursor.fetchone()

async def add_referral_earning(user_id, amount):
    """Добавить реферальный заработок"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('UPDATE users SET ref_earned = COALESCE(ref_earned, 0) + ? WHERE user_id = ?', (amount, user_id))
        await db.commit()

async def get_referrer(user_id):
    """Получить реферера"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_expired_subscriptions():
    """Получить все истекшие активные подписки (по дате или трафику)"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            '''SELECT * FROM subscriptions 
               WHERE is_active = 1 
               AND datetime(expires_at) <= datetime('now')
               ORDER BY expires_at ASC
               LIMIT 100''',
        ) as cursor:
            return await cursor.fetchall()

async def get_all_active_subscriptions():
    """Получить все активные подписки для проверки в панели"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            '''SELECT * FROM subscriptions 
               WHERE is_active = 1
               ORDER BY created_at DESC''',
        ) as cursor:
            return await cursor.fetchall()

async def deactivate_subscription(sub_id):
    """Деактивировать подписку"""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('UPDATE subscriptions SET is_active = 0 WHERE id = ?', (sub_id,))
        await db.commit()
