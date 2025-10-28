import sqlite3

def init_db():
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            buyer_id INTEGER,
            gift_name TEXT,
            price TEXT,
            status TEXT DEFAULT 'waiting_buyer'
        )
    """)
    conn.commit()
    conn.close()

def create_deal(seller_id, gift_name, price):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO deals (seller_id, gift_name, price) VALUES (?, ?, ?)",
                (seller_id, gift_name, price))
    conn.commit()
    conn.close()

def get_deals_by_status(status):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("SELECT id, seller_id, gift_name, price FROM deals WHERE status=?", (status,))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_deal_status(deal_id, status, buyer_id=None):
    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    if buyer_id:
        cur.execute("UPDATE deals SET status=?, buyer_id=? WHERE id=?", (status, buyer_id, deal_id))
    else:
        cur.execute("UPDATE deals SET status=? WHERE id=?", (status, deal_id))
    conn.commit()
    conn.close()

def get_deal_by_id(deal_id):
    conn = sqlite3.connect("deals.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, seller_id, buyer_id, gift_name, price, status FROM deals WHERE id = ?", (deal_id,))
    deal = cursor.fetchone()
    conn.close()
    if deal:
        # Превращаем результат в объект с удобными полями
        return Deal(*deal)
    return None

class Deal:
    def __init__(self, id, seller_id, buyer_id, gift_name, price, status):
        self.id = id
        self.seller_id = seller_id
        self.buyer_id = buyer_id
        self.gift_name = gift_name
        self.price = price
        self.status = status