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

# کلمات کلیدی برای تشخیص درآمد (اگر این کلمات باشند، تراکنش مثبت ثبت می‌شود)
INCOME_KEYWORDS = ["حقوق", "درآمد", "واریز", "فروش", "سود", "هدیه", "طلب", "برگشتی", "پاداش", "یارانه"]

# دسته‌بندی هوشمند بر اساس کلمات موجود در متن
CATEGORIES = {
    "🍎 تغذیه": ["غذا", "رستوران", "سوپرمارکت", "نون", "میوه", "ناهار", "شام", "کافه", "سیگار", "شیرینی", "گوشت", "مرغ"],
    "🚗 حمل و نقل": ["بنزین", "اسنپ", "تپسی", "ماشین", "تعمیرگاه", "کارواش", "مترو", "اتوبوس", "پارکینگ"],
    "🏠 خانه": ["اجاره", "شارژ", "قبض", "آب", "برق", "گاز", "اینترنت", "تعمیرات خانه", "خرید وسایل"],
    "💊 سلامت": ["دکتر", "دارو", "ویزیت", "داروخانه", "بیمارستان", "دندانپزشکی"],
    "💳 مالی و قسط": ["قسط", "وام", "کارت به کارت", "قرض", "بدهی", "چک", "بیمه"],
    "👕 پوشاک": ["لباس", "کفش", "شلوار", "پیراهن", "آرایشگاه"],
    "🎮 تفریح": ["سینما", "بازی", "سفر", "هتل", "بلیط"]
}

# تابع مدیریت دیتابیس جداگانه برای هر کاربر
def get_db(user_id):
    db_path = f"user_{user_id}.db"
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS tx 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  amount INTEGER, desc TEXT, type TEXT, category TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    return conn

# تشخیص خودکار دسته‌بندی
def detect_category(text):
    for cat, words in CATEGORIES.items():
        if any(w in text for w in words):
            return cat
    return "📝 سایر"

# استخراج عدد از متن (تبدیل فینگلیش یا کلمات به عدد)
def extract_amount(text):
    text = text.replace("میلیون", "000000").replace("ملیون", "000000").replace("هزار", "000").replace("تومن", "").replace("تومان", "")
    nums = re.findall(r'\d+', text.replace(',', ''))
    return int("".join(nums)) if nums else None

# پردازش نهایی متن و ذخیره در دیتابیس
async def process_data(user_id, text):
    amount = extract_amount(text)
    if not amount:
        return f"❓ مبلغی در این متن پیدا نشد:\n«{text}»\n(مثال: ۲۰۰ هزار تومن ناهار)"
    
    # تشخیص نوع (درآمد یا هزینه)
    is_income = any(w in text for w in INCOME_KEYWORDS)
    tx_type = "درآمد ➕" if is_income else "هزینه ➖"
    category = detect_category(text)
    
    # ذخیره مبلغ (هزینه به صورت منفی ذخیره می‌شود تا در جمع کل درست عمل کند)
    final_amount = amount if is_income else -amount

    conn = get_db(user_id)
    conn.execute("INSERT INTO tx (amount, desc, type, category) VALUES (?, ?, ?, ?)", 
                 (final_amount, text, tx_type, category))
    conn.commit()
    conn.close()
    
    return f"✅ {tx_type} ثبت شد:\n💰 مبلغ: {amount:,} تومان\n🗂 دسته: {category}\n📝 بابت: {text}"

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["📊 موجودی فعلی", "📥 خروجی اکسل"]]
    await update.message.reply_text(
        "🌟 به **جیبی‌نو** خوش آمدید!\n\nمن حسابدار شخصی شما هستم. کافیست مخارج یا درآمدهای خود را به صورت متن یا ویس بفرستید تا ثبت کنم.\n\nمثلاً: «۵۰ هزار تومان کرایه تاکسی» یا «۱۲ میلیون حقوق واریز شد»",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="Markdown"
    )

# تهیه فایل اکسل گزارش
async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(uid)
    df = pd.read_sql_query("SELECT date as 'تاریخ', type as 'نوع', amount as 'مبلغ (تومان)', category as 'دسته', desc as 'توضیحات' FROM tx ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        return await update.message.reply_text("❌ هنوز هیچ تراکنشی ثبت نکرده‌اید.")
    
    file_path = f"report_{uid}.xlsx"
    df.to_excel(file_path, index=False)
    
    await update.message.reply_document(
        document=open(file_path, 'rb'),
        caption="📊 گزارش مالی کامل شما با تفکیک دسته‌بندی"
    )
    os.remove(file_path)

# مشاهده موجودی کل
async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db(update.effective_user.id)
    df = pd.read_sql_query("SELECT amount FROM tx", conn)
    conn.close()
    total = df['amount'].sum() if not df.empty else 0
    
    status = "🔴 بدهکار/منفی" if total < 0 else "🟢 مثبت"
    await update.message.reply_text(f"💰 **مانده کل حساب شما:**\n\n{total:,} تومان\nوضعیت: {status}", parse_mode="Markdown")

# تبدیل ویس به متن و پردازش
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = await update.message.reply_text("⏳ در حال گوش دادن به ویس شما...")
    ogg_file = f"v_{update.effective_user.id}.ogg"
    wav_file = f"v_{update.effective_user.id}.wav"
    
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive(ogg_file)
        
        # تبدیل فرمت ogg به wav برای شناسایی توسط گوگل
        AudioSegment.from_ogg(ogg_file).export(wav_file, format="wav")
        
        r = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="fa-IR")
        
        result = await process_data(update.effective_user.id, text)
        await m.edit_text(result)
        
    except Exception as e:
        await m.edit_text(f"❌ متاسفم، متوجه صدات نشدم. دوباره امتحان کن.\n(خطا: {str(e)})")
    finally:
        if os.path.exists(ogg_file): os.remove(ogg_file)
        if os.path.exists(wav_file): os.remove(wav_file)

# تابع اصلی اجرای ربات
def main():
    print("--- JibiNo Bot is Running... ---")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("📥 خروجی اکسل"), export_excel))
    app.add_handler(MessageHandler(filters.Text("📊 موجودی فعلی"), get_balance))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text(process_data(u.effective_user.id, u.message.text))))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    app.run_polling()

if __name__ == '__main__':
    main()
