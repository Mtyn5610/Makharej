import sqlite3

def init_db():
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()

    # جدول کاربران
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        daily_count INTEGER DEFAULT 0,
        last_reset TEXT,
        is_vip BOOLEAN DEFAULT FALSE,
        vip_expire_date TEXT
    )''')

    # جدول تراکنش‌ها (هزینه و درآمد)
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        user_id INTEGER,
        amount INTEGER,
        category TEXT,
        description TEXT,
        type TEXT,
        date TEXT
    )''')

    # جدول دارایی‌ها (طلا و ارز)
    cursor.execute('''CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        user_id INTEGER,
        asset_name TEXT,
        amount REAL,
        buy_price INTEGER,
        current_price INTEGER,
        date TEXT
    )''')

    conn.commit()
    conn.close()
