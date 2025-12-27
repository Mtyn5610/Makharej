import os, sqlite3, pandas as pd, re, whisper
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "ENTER_TOKEN_HERE"
model = whisper.load_model("tiny")

# تابع داخلی برای تبدیل کلمات فارسی به عدد (جایگزین کتابخانه خارجی)
def persian_to_int(text):
    words = {
        'یک': 1, 'دو': 2, 'سه': 3, 'چهار': 4, 'پنج': 5, 'شش': 6, 'هفت': 7, 'هشت': 8, 'نه': 9, 'ده': 10,
        'بیست': 20, 'سی': 30, 'چهل': 40, 'پنجاه': 50, 'شصت': 60, 'هفتاد': 70, 'هشتاد': 80, 'نود': 90,
        'صد': 100, 'دویست': 200, 'سیصد': 300, 'چهارصد': 400, 'پانصد': 500, 'ششصد': 600, 'هفتصد': 700, 'هشتصد': 800, 'نهصد': 900,
        'هزار': 1000, 'میلیون': 1000000
    }
    # ابتدا اعداد دیجیتالی را چک کن
    nums = re.findall(r'\d+', text.replace(',', ''))
    if nums: return int(nums[0])
    
    # اگر عدد دیجیتالی نبود، کلمات را چک کن
    total = 0
    current = 0
    for word in text.split():
        if word in words:
            val = words[word]
            if val >= 1000:
                if current == 0: current = 1
                total += current * val
                current = 0
            else:
                current += val
    return total + current if (total + current) > 0 else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["📊 گزارش کلی", "📥 دریافت فایل اکسل"]]
    await update.message.reply_text("سلام! مبلغ را بگویید یا بنویسید.", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def process_data(user_id, text):
    amount = persian_to_int(text)
    if not amount: return "❌ مبلغی پیدا نشد."
    
    is_income = any(w in text for w in ["حقوق", "درآمد", "واریز", "فروش"])
    tx_type = "درآمد ➕" if is_income else "هزینه ➖"
    val = amount if is_income else -amount

    conn = sqlite3.connect(f"user_{user_id}.db")
    conn.execute("CREATE TABLE IF NOT EXISTS tx (id INTEGER PRIMARY KEY AUTOINCREMENT, amount INTEGER, desc TEXT, type TEXT)")
    conn.execute("INSERT INTO tx (amount, desc, type) VALUES (?, ?, ?)", (val, text, tx_type))
    conn.commit()
    conn.close()
    return f"✅ ثبت شد: {amount:,} تومان ({tx_type})"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = await process_data(update.effective_user.id, update.message.text)
    await update.message.reply_text(res)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = await update.message.reply_text("⏳ در حال پردازش صدا...")
    f = await context.bot.get_file(update.message.voice.file_id)
    await f.download_to_drive("v.ogg")
    res = model.transcribe("v.ogg", language="fa")
    answer = await process_data(update.effective_user.id, res["text"])
    await m.edit_text(answer)
    if os.path.exists("v.ogg"): os.remove("v.ogg")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()

if __name__ == '__main__': main()    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["📊 گزارش کلی", "📥 دریافت فایل اکسل"]]
    await update.message.reply_text(
        "سلام! من حسابدار هوشمند شما هستم.\n\n"
        "💰 مبلغ را بنویسید یا ویس بفرستید.\n"
        "مثال: «۵۰ هزار تومان بنزین» یا «۲ میلیون واریز حقوق»", 
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def process_data(user_id, text):
    amount = extract_amount(text)
    if not amount:
        return "❌ مبلغی پیدا نشد! لطفاً مبلغ را به عدد یا حروف واضح (مثلاً بیست هزار) بگویید."
    
    # تشخیص نوع تراکنش
    is_income = any(w in text for w in ["حقوق", "درآمد", "واریز", "فروش", "هدیه"])
    tx_type = "درآمد ➕" if is_income else "هزینه ➖"
    val = amount if is_income else -amount

    conn = get_db(user_id)
    conn.execute("INSERT INTO tx (amount, desc, type) VALUES (?, ?, ?)", (val, text, tx_type))
    conn.commit()
    conn.close()
    
    return f"✅ ثبت شد:\n💰 مبلغ: {amount:,} تومان\n🗂 نوع: {tx_type}\n📝 متن: {text}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await process_data(update.effective_user.id, update.message.text)
    await update.message.reply_text(response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent_msg = await update.message.reply_text("🎧 در حال شنیدن صدای شما...")
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        path = f"voice_{update.effective_user.id}.ogg"
        await file.download_to_drive(path)
        
        # تبدیل صوت به متن
        result = model.transcribe(path, language="fa")
        text = result["text"]
        
        response = await process_data(update.effective_user.id, text)
        await sent_msg.edit_text(response)
        
        if os.path.exists(path): os.remove(path)
    except Exception as e:
        await sent_msg.edit_text(f"❌ خطای فنی در پردازش صدا: {str(e)}")

async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db(user_id)
    df = pd.read_sql_query("SELECT amount FROM tx", conn)
    conn.close()
    
    total = df['amount'].sum() if not df.empty else 0
    await update.message.reply_text(f"📊 گزارش موجودی:\n💰 مانده نهایی: {total:,} تومان")

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db(user_id)
    df = pd.read_sql_query("SELECT * FROM tx", conn)
    conn.close()
    
    if df.empty:
        await update.message.reply_text("داده‌ای برای خروجی وجود ندارد.")
        return
        
    path = f"report_{user_id}.xlsx"
    df.to_excel(path, index=False)
    await update.message.reply_document(open(path, 'rb'), caption="📊 لیست کامل تراکنش‌های شما")
    if os.path.exists(path): os.remove(path)

def main():
    print("🚀 ربات با موفقیت در حال اجرا است...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("📊 گزارش کلی"), send_report))
    app.add_handler(MessageHandler(filters.Text("📥 دریافت فایل اکسل"), export_excel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()

if __name__ == '__main__':
    main()    conn.commit()
    conn.close()
    return f"✅ ثبت شد: {amount:,} تومان ({tx_type})\n📝 متن تشخیص داده شده: {text}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await process_data(update.effective_user.id, update.message.text)
    await update.message.reply_text(response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent_msg = await update.message.reply_text("🎧 در حال گوش دادن به صدای شما...")
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive("voice.ogg")
        
        # تشخیص گفتار با مدل Whisper
        result = model.transcribe("voice.ogg", language="fa")
        text = result["text"]
        
        response = await process_data(update.effective_user.id, text)
        await sent_msg.edit_text(response)
    except Exception as e:
        await sent_msg.edit_text(f"❌ خطا در پردازش صدا: {str(e)}")
    finally:
        if os.path.exists("voice.ogg"): os.remove("voice.ogg")

async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db(user_id)
    df = pd.read_sql_query("SELECT amount FROM tx", conn)
    total = df['amount'].sum() if not df.empty else 0
    await update.message.reply_text(f"💰 موجودی کل شما: {total:,} تومان")
    conn.close()

def main():
    print("🤖 ربات با موفقیت فعال شد...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("📊 گزارش کلی"), send_report))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.run_polling()

if __name__ == '__main__':
    main()
