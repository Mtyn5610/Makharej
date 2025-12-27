import os, sqlite3, re, pandas as pd, speech_recognition as sr
from pydub import AudioSegment
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- پیکربندی ---
TOKEN = "ENTER_TOKEN_HERE"

# لیست کلمات برای تشخیص هوشمند درآمد
INCOME_KEYWORDS = ["حقوق", "درآمد", "واریز", "فروش", "سود", "هدیه", "طلب", "برگشتی", "پاداش"]

# دسته‌بندی خودکار
CATEGORIES = {
    "🍎 تغذیه": ["غذا", "رستوران", "سوپرمارکت", "نون", "میوه", "ناهار", "شام", "کافه", "سیگار", "شیرینی"],
    "🚗 حمل و نقل": ["بنزین", "اسنپ", "تپسی", "ماشین", "تعمیرگاه", "کارواش", "مترو", "اتوبوس"],
    "🏠 خانه": ["اجاره", "شارژ", "قبض", "آب", "برق", "گاز", "اینترنت", "تعمیرات"],
    "💊 سلامت": ["دکتر", "دارو", "ویزیت", "داروخانه", "بیمارستان"],
    "💳 مالی": ["قسط", "وام", "کارت به کارت", "قرض", "بدهی"]
}

def get_db(user_id):
    conn = sqlite3.connect(f"user_{user_id}.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tx 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  amount INTEGER, desc TEXT, type TEXT, category TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    return conn

def detect_category(text):
    for cat, words in CATEGORIES.items():
        if any(w in text for w in words): return cat
    return "📝 سایر"

def extract_amount(text):
    text = text.replace("میلیون", "000000").replace("ملیون", "000000").replace("هزار", "000").replace("تومن", "").replace("تومان", "")
    nums = re.findall(r'\d+', text.replace(',', ''))
    return int("".join(nums)) if nums else None

async def process_data(user_id, text):
    amount = extract_amount(text)
    if not amount: return f"❓ مبلغی در این متن پیدا نشد:\n«{text}»"
    
    is_income = any(w in text for w in INCOME_KEYWORDS)
    tx_type = "درآمد ➕" if is_income else "هزینه ➖"
    category = detect_category(text)
    final_amount = amount if is_income else -amount

    conn = get_db(user_id)
    conn.execute("INSERT INTO tx (amount, desc, type, category) VALUES (?, ?, ?, ?)", 
                 (final_amount, text, tx_type, category))
    conn.commit()
    conn.close()
    
    return f"✅ {tx_type} ثبت شد:\n💰 مبلغ: {amount:,} تومان\n🗂 دسته: {category}\n📝 بابت: {text}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["📊 موجودی فعلی", "📥 خروجی اکسل"]]
    await update.message.reply_text(
        "🌟 به جیبی‌نو خوش آمدید!\nمن مخارج و درآمدهای شما را مدیریت می‌کنم.\nکافیست مبلغ را بنویسید یا ویس بفرستید.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(uid)
    df = pd.read_sql_query("SELECT date as 'تاریخ', type as 'نوع', amount as 'مبلغ', category as 'دسته', desc as 'توضیح' FROM tx", conn)
    conn.close()
    if df.empty: return await update.message.reply_text("❌ هنوز تراکنشی ثبت نکرده‌اید.")
    
    file_path = f"report_{uid}.xlsx"
    df.to_excel(file_path, index=False)
    await update.message.reply_document(open(file_path, 'rb'), caption="📊 گزارش مالی کامل شما")
    os.remove(file_path)

async def get_balance(update
