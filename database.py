import sqlite3

class DatabaseManager:
    def __init__(self, db_path='jibino.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        """ساخت جداول مورد نیاز برای ذخیره تراکنش‌ها"""
        query = '''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            asset_type TEXT,
            amount REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.conn.execute(query)
        self.conn.commit()

    def add_transaction(self, user_id, asset_type, amount):
        """ثبت خرید یا موجودی جدید"""
        query = 'INSERT INTO transactions (user_id, asset_type, amount) VALUES (?, ?, ?)'
        self.conn.execute(query, (user_id, asset_type, amount))
        self.conn.commit()

    def get_balance(self, user_id):
        """محاسبه مجموع دارایی‌ها به تفکیک نوع"""
        categories = ['gold', 'asset'] # طلا و سایر دارایی‌ها (ارز/سکه)
        balances = {}
        
        for cat in categories:
            query = 'SELECT SUM(amount) FROM transactions WHERE user_id = ? AND asset_type = ?'
            result = self.conn.execute(query, (user_id, cat)).fetchone()
            balances[cat] = result[0] if result[0] else 0
            
        return balances
