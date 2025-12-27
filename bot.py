#!/usr/bin/env python3
import os
import sqlite3
import re
import pandas as pd
import speech_recognition as sr
from pydub import AudioSegment
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات اصلی ---
TOKEN = "ENTER_TOKEN_HERE"

# کلمات کلیدی درآمد (گسترش یافته برای تشخیص دقیق‌تر)
INCOME_KEYWORDS = [
    "حقوق", "درآمد", "واریز", "فروش", "فروختم", "سود", "هدیه", "طلب", "برگشتی", 
    "پاداش", "یارانه", "دریافت", "گرفتم", "اومد", "نشست", "کاسبی", "دستمزد"
]

# دسته‌بندی هوشمند (گسترش یافته)
CATEGORIES = {
    "🍎 تغذیه": ["غذا", "رستوران", "سوپرمارکت", "نون", "میوه", "ناهار", "شام", "کافه", "سیگار", "شیرینی", "گوشت", "مرغ", "هایپر", "لبنیات"],
    "💰 سرمایه‌گذاری": ["طلا", "دلار", "ارز", "سکه", "بورس", "سهام", "کریپتو", "تتر", "بیت کوین"],
    "🚗 حمل و نقل": ["بنزین", "اسنپ", "تپسی", "ماشین", "تعمیرگاه", "کارواش", "مترو", "اتوبوس", "پارکینگ", "لاستیک", "روغن"],
    "🏠 خانه": ["اجاره", "شارژ", "قبض", "آب", "برق", "گاز", "اینترنت", "تلفن", "وسایل خونه", "تعمیرات"],
    "💊 سلامت": ["دکتر", "دارو", "ویزیت", "داروخانه", "فیزیوتراپی", "بیمارستان", "آزمایشگاه", "دندون"],
    "💳 مالی و قسط": ["قسط", "وام", "کارت به کارت", "قرض", "بدهی", "چک", "بیمه", "مالیات"],
    "👕 پوشاک و آرایش": ["لباس", "کفش", "شلوار", "پیراهن", "آرایشگاه", "سلمانی", "پیرایش", "ادکلن"],
    "🎮 تفریح و هدیه": ["سینما", "بازی", "سفر", "هتل", "بلیط", "کادو", "تولد", "مهمونی", "کنسرت"],
    "📱 تکنولوژی": ["موبایل", "گوشی", "شارژر", "لپ‌تاپ", "هدفون", "نرم‌افزار", "آنتی ویروس"]
}

# --- مدیریت دیتابیس ---
def get_db(user_id):
    db_path = f"user_{user_id}.db"
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS tx 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  amount INTEGER, desc TEXT, type TEXT, category TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    return conn

def extract_amount(text):
    text = text.replace("میلیون", "000000").replace("ملیون", "000000").replace("هزار", "000").replace("تومن", "").replace("تومان", "")
    nums = re.findall(r'\d+', text.replace(',', ''))
    return int("".join(nums)) if nums else None

def detect_category(text):
    for cat, words in CATEGORIES.items():
        if any(w in text for w in words):
            return cat
    return "📝 سایر"

async def process_data(user_id, text):
    amount = extract_amount(text)
    if not amount:
        return f"❓ مبلغی در این متن پیدا نشد:\n«{text}»"
    
    # تشخیص هوشمند نوع تراکنش
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

# --- دستورات ربات ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        ["📊 موجودی و گزارش", "📥 خروجی اکسل"],
        ["🗑 حذف آخرین ثبت", "⚠️ پاکسازی کل"]
    ]
    await update.message.reply_text(
        "🌟 به **جیبی‌نو** خوش آمدید!\n\nمن با کلمات جدید آپدیت شدم! کافیه مخارج یا درآمدت رو بگی.\nمثلاً: «گوشیم رو ۵ میلیون فروختم» یا «۲۰ تومن پول شارژر دادم»",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="Markdown"
    )

async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(uid)
    df_all = pd.read_sql_query("SELECT amount FROM tx", conn)
    total = df_all['amount'].sum() if not df_all.empty else 0
    
    df_cat = pd.read_sql_query("SELECT category, SUM(amount) as cat_sum FROM tx WHERE amount < 0 GROUP BY category", conn)
    conn.close()

    report = f"💰 **گزارش وضعیت مالی شما**\n---------------------------------------\n"
    report += f"💵 **مانده کل:** {total:,} تومان\n\n"
    
    if not df_cat.empty:
        report += "🔻 **بیشترین هزینه‌ها به تفکیک:**\n"
        for _, row in df_cat.iterrows():
            report += f"{row['category']}: {abs(row['cat_sum']):,} تومان\n"
    
    await update.message.reply_text(report, parse_mode="Markdown")

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(uid)
    df = pd.read_sql_query("SELECT date, type, amount, category, desc FROM tx ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        return await update.message.reply_text("❌ دیتابیس خالی است.")
    
    path = f"report_{uid}.xlsx"
    df.to_excel(path, index=False)
    await update.message.reply_document(document=open(path, 'rb'), caption="📊 گزارش کامل اکسل")
    os.remove(path)

async def delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(uid)
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, desc FROM tx ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM tx WHERE id = ?", (row[0],))
        conn.commit()
        await update.message.reply_text(f"🗑 تراکنش حذف شد:\n{row[2]} ({abs(row[1]):,} تومان)")
    else:
        await update.message.reply_text("تراکنشی یافت نشد.")
    conn.close()

async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(uid)
    conn.execute("DELETE FROM tx")
    conn.commit()
    conn.close()
    await update.message.reply_text("⚠️ تمام اطلاعات شما پاک شد.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = await update.message.reply_text("⏳ در حال پردازش صوت...")
    ogg = f"v_{update.effective_user.id}.ogg"
    wav = f"v_{update.effective_user.id}.wav"
    try:
        f = await context.bot.get_file(update.message.voice.file_id)
        await f.download_to_drive(ogg)
        AudioSegment.from_ogg(ogg).export(wav, format="wav")
        r = sr.Recognizer()
        with sr.AudioFile(wav) as source:
            text = r.recognize_google(r.record(source), language="fa-IR")
        res = await process_data(update.effective_user.id, text)
        await m.edit_text(res)
    except Exception:
        await m.edit_text("❌ متوجه صدا نشدم.")
    finally:
        for f in [ogg, wav]: 
            if os.path.exists(f): os.remove(f)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = await process_data(update.effective_user.id, update.message.text)
    await update.message.reply_text(res)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("📊 موجودی و گزارش"), get_balance))
    app.add_handler(MessageHandler(filters.Text("📥 خروجی اکسل"), export_excel))
    app.add_handler(MessageHandler(filters.Text("🗑 حذف آخرین ثبت"), delete_last))
    app.add_handler(MessageHandler(filters.Text("⚠️ پاکسازی کل"), clear_all))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("JibiNo is online with extended vocabulary...")
    app.run_polling()

if __name__ == '__main__':
    main()
