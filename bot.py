import os
import sqlite3
import pandas as pd
import logging
import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تنظیمات لاگ برای مشاهده فعالیت ربات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# این عبارت توسط اسکریپت نصب (install.sh) با توکن واقعی جایگزین می‌شود
TOKEN = "ENTER_TOKEN_HERE"

# --- مدیریت دیتابیس اختصاصی برای هر کاربر ---
def get_db(user_id):
    db_name = f"user_{user_id}.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      amount INTEGER, description TEXT, category TEXT)''')
    conn.commit()
    return conn

# --- دستورات اصلی ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📊 گزارش", "📥 دریافت اکسل"], ["❓ راهنما"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"سلام {update.effective_user.first_name}! 💰\nخوش آمدی. مبلغ و بابت هزینه‌ات را بفرست (مثلاً: ۵۰ تومن بنزین)",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    # استخراج اولین عدد از متن به عنوان مبلغ
    numbers = re.findall(r'\d+', text)
    if not numbers:
        await update.message.reply_text("❌ مبلغی در پیام شما پیدا نشد.")
        return
    
    amount = int(numbers[0])
    category = "سایر 📦"
    if any(word in text for word in ["غذا", "رستوران", "نون"]): category = "خوراک 🛒"
    elif any(word in text for word in ["بنزین", "اسنپ", "کرایه"]): category = "تردد 🚗"

    conn = get_db(user_id)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (amount, description, category) VALUES (?, ?, ?)", 
                   (amount, text, category))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ مبلغ {amount:,} تومان در دسته '{category}' ثبت شد.")

async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db(user_id)
    df = pd.read_sql_query("SELECT category, SUM(amount) as total FROM transactions GROUP BY category", conn)
    conn.close()

    if df.empty:
        await update.message.reply_text("📜 لیست هزینه‌های شما خالی است.")
        return

    total_sum = df['total'].sum()
    msg = "📊 **گزارش هزینه‌ها:**\n\n"
    msg += "```\n"
    for _, row in df.iterrows():
        percent = (row['total'] / total_sum) * 100
        msg += f"{row['category']:<10} | {row['total']:,} | {percent:.1f}%\n"
    msg += "```\n"
    msg += f"💰 **جمع کل: {total_sum:,} تومان**"
    await update.message.reply_text(msg, parse_mode="MarkdownV2")

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db(user_id)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    
    if df.empty:
        await update.message.reply_text("❌ داده‌ای برای خروجی وجود ندارد.")
        return

    file_path = f"report_{user_id}.xlsx"
    df.to_excel(file_path, index=False)
    await update.message.reply_document(document=open(file_path, 'rb'), filename="My_Finance.xlsx")
    os.remove(file_path)

# --- اجرای ربات ---
def main():
    if TOKEN == "ENTER_TOKEN_HERE":
        print("❌ خطا: توکن تنظیم نشده است!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("📊 گزارش"), send_report))
    app.add_handler(MessageHandler(filters.Text("📥 دریافت اکسل"), export_excel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 ربات در حال اجراست...")
    app.run_polling()

if __name__ == '__main__':
    main()
