import os, sqlite3, pandas as pd, re, whisper
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "ENTER_TOKEN_HERE"
# بارگذاری مدل هوش مصنوعی (ممکن است چند لحظه طول بکشد)
model = whisper.load_model("base")

def get_db(user_id):
    conn = sqlite3.connect(f"user_{user_id}.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tx (id INTEGER PRIMARY KEY AUTOINCREMENT, amount INTEGER, desc TEXT, type TEXT)''')
    return conn

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["📊 گزارش کلی", "📥 دریافت فایل اکسل"]]
    await update.message.reply_text("سلام! مبلغ را بنویس یا جزییات را بصورت ویس بگو (مثلاً: ۵۰ هزار تومان بابت حقوق)", 
                                  reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def process_data(user_id, text):
    nums = re.findall(r'\d+', text.replace(',', ''))
    if not nums: return "❌ مبلغی در پیام شما پیدا نشد."
    
    amount = int(nums[0])
    tx_type = "درآمد ➕" if any(w in text for w in ["حقوق", "درآمد", "واریز", "فروش"]) else "هزینه ➖"
    val = amount if tx_type == "درآمد ➕" else -amount

    conn = get_db(user_id)
    conn.execute("INSERT INTO tx (amount, desc, type) VALUES (?, ?, ?)", (val, text, tx_type))
    conn.commit()
    return f"✅ ثبت شد: {amount:,} تومان ({tx_type})\n📝 متن: {text}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await process_data(update.effective_user.id, update.message.text)
    await update.message.reply_text(response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent_msg = await update.message.reply_text("⏳ در حال گوش دادن به ویس شما...")
    file = await context.bot.get_file(update.message.voice.file_id)
    await file.download_to_drive("voice.ogg")
    
    # تبدیل صوت به متن
    result = model.transcribe("voice.ogg", language="fa")
    text = result["text"]
    
    response = await process_data(update.effective_user.id, text)
    await sent_msg.edit_text(response)
    if os.path.exists("voice.ogg"): os.remove("voice.ogg")

async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db(user_id)
    df = pd.read_sql_query("SELECT amount FROM tx", conn)
    total = df['amount'].sum() if not df.empty else 0
    await update.message.reply_text(f"💰 موجودی فعلی: {total:,} تومان")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("📊 گزارش کلی"), send_report))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()

if __name__ == '__main__': main()    user_id = update.effective_user.id
    
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
