import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    
    # Таблица сделок - ОБНОВЛЕНО: добавлены username
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            seller_username TEXT,
            buyer_id INTEGER,
            buyer_username TEXT,
            gift_name TEXT,
            price TEXT,
            status TEXT DEFAULT 'waiting_buyer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица пользователей (баланс и рейтинг)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            rating REAL DEFAULT 5.0,
            deals_count INTEGER DEFAULT 0,
            is_frozen BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица транзакций
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT, -- 'deposit', 'withdrawal', 'payment', 'income'
            description TEXT,
            status TEXT DEFAULT 'completed', -- 'completed', 'pending', 'cancelled'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица рейтингов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            deal_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Функция миграции для добавления username к существующим сделкам
def migrate_old_deals():
    """Добавляем username к существующим сделкам"""
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    
    # Проверяем, есть ли столбцы seller_username и buyer_username
    try:
        cur.execute("SELECT seller_username FROM deals LIMIT 1")
    except sqlite3.OperationalError:
        # Добавляем столбцы если их нет
        cur.execute("ALTER TABLE deals ADD COLUMN seller_username TEXT")
        cur.execute("ALTER TABLE deals ADD COLUMN buyer_username TEXT")
        conn.commit()
        print("✅ Добавлены столбцы username в таблицу deals")
    
    # Для существующих сделок без seller_username
    cur.execute("SELECT id, seller_id FROM deals WHERE seller_username IS NULL OR seller_username = ''")
    deals = cur.fetchall()
    
    for deal_id, seller_id in deals:
        try:
            # Получаем username из таблицы users
            cur.execute("SELECT username FROM users WHERE user_id=?", (seller_id,))
            user = cur.fetchone()
            if user and user[0]:
                cur.execute("UPDATE deals SET seller_username=? WHERE id=?", (user[0], deal_id))
                print(f"✅ Обновлен seller_username для сделки #{deal_id}")
        except Exception as e:
            print(f"❌ Ошибка миграции сделки #{deal_id}: {e}")
    
    # Для существующих сделок без buyer_username но с buyer_id
    cur.execute("SELECT id, buyer_id FROM deals WHERE buyer_id IS NOT NULL AND (buyer_username IS NULL OR buyer_username = '')")
    deals_with_buyer = cur.fetchall()
    
    for deal_id, buyer_id in deals_with_buyer:
        try:
            # Получаем username из таблицы users
            cur.execute("SELECT username FROM users WHERE user_id=?", (buyer_id,))
            user = cur.fetchone()
            if user and user[0]:
                cur.execute("UPDATE deals SET buyer_username=? WHERE id=?", (user[0], deal_id))
                print(f"✅ Обновлен buyer_username для сделки #{deal_id}")
        except Exception as e:
            print(f"❌ Ошибка миграции buyer для сделки #{deal_id}: {e}")
    
    conn.commit()
    conn.close()

# Функции для пользователей
def get_or_create_user(user_id, username=None):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", 
                   (user_id, username))
        conn.commit()
    else:
        # Обновляем username если он изменился
        if username and username != user[1]:
            cur.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
            conn.commit()
    
    conn.close()
    return user

def get_user_balance(user_id):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 0

def update_user_balance(user_id, amount):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def get_user_rating(user_id):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("SELECT rating, deals_count FROM users WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result if result else (5.0, 0)

def update_user_rating(user_id, new_rating):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    
    # Получаем текущий рейтинг и количество сделок
    cur.execute("SELECT rating, deals_count FROM users WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    if not result:
        return
    
    current_rating, deals_count = result
    
    # Обновляем рейтинг (среднее арифметическое)
    new_avg_rating = (current_rating * deals_count + new_rating) / (deals_count + 1)
    
    cur.execute("UPDATE users SET rating = ?, deals_count = deals_count + 1 WHERE user_id=?", 
               (new_avg_rating, user_id))
    conn.commit()
    conn.close()

# Функции для транзакций
def add_transaction(user_id, amount, transaction_type, description):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (user_id, amount, type, description) 
        VALUES (?, ?, ?, ?)
    """, (user_id, amount, transaction_type, description))
    conn.commit()
    conn.close()

def get_user_transactions(user_id, limit=10):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT amount, type, description, created_at 
        FROM transactions 
        WHERE user_id=? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (user_id, limit))
    transactions = cur.fetchall()
    conn.close()
    return transactions

# Админ функции
def get_all_users():
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, balance, rating, is_frozen FROM users")
    users = cur.fetchall()
    conn.close()
    return users

def admin_update_balance(user_id, amount):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def toggle_user_freeze(user_id):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_frozen = NOT is_frozen WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ОБНОВЛЕННЫЕ функции для сделок
class Deal:
    def __init__(self, id, seller_id, seller_username, buyer_id, buyer_username, gift_name, price, status):
        self.id = id
        self.seller_id = seller_id
        self.seller_username = seller_username or ""
        self.buyer_id = buyer_id
        self.buyer_username = buyer_username or ""
        self.gift_name = gift_name
        self.price = price
        self.status = status

# ОБНОВЛЕНО: сохраняем username продавца
def create_deal(seller_id, seller_username, gift_name, price):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO deals (seller_id, seller_username, gift_name, price) VALUES (?, ?, ?, ?)",
                (seller_id, seller_username, gift_name, price))
    conn.commit()
    conn.close()

# ОБНОВЛЕНО: возвращаем username
def get_deals_by_status(status):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("SELECT id, seller_id, seller_username, gift_name, price FROM deals WHERE status=?", (status,))
    rows = cur.fetchall()
    conn.close()
    return rows

# ОБНОВЛЕНО: отдельная функция для установки покупателя с username
def update_deal_buyer(deal_id, buyer_id, buyer_username):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("UPDATE deals SET buyer_id=?, buyer_username=?, status='waiting_payment' WHERE id=?", 
                (buyer_id, buyer_username, deal_id))
    conn.commit()
    conn.close()

def update_deal_status(deal_id, status):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("UPDATE deals SET status=? WHERE id=?", (status, deal_id))
    conn.commit()
    conn.close()

# ОБНОВЛЕНО: получаем все данные включая username
def get_deal_by_id(deal_id):
    conn = sqlite3.connect("deals.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, seller_id, seller_username, buyer_id, buyer_username, gift_name, price, status FROM deals WHERE id = ?", (deal_id,))
    deal = cursor.fetchone()
    conn.close()
    if deal:
        return Deal(*deal)
    return None

# ОБНОВЛЕНО: получаем сделки пользователя с username
def get_user_deals(user_id):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT id, seller_id, seller_username, buyer_id, buyer_username, gift_name, price, status, created_at
        FROM deals 
        WHERE seller_id=? OR buyer_id=?
        ORDER BY created_at DESC
    """, (user_id, user_id))
    deals = cur.fetchall()
    conn.close()
    return deals
