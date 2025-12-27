import os, sqlite3, pandas as pd, re, whisper
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from word2number_fa import persian_w2n

TOKEN = "ENTER_TOKEN_HERE"
# استفاده از مدل tiny برای سرعت و بهینه‌سازی رم سرور
model = whisper.load_model("tiny")

def get_db(user_id):
    conn = sqlite3.connect(f"user_{user_id}.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tx 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      amount INTEGER, desc TEXT, type TEXT)''')
    return conn

def extract_amount(text):
    # اول: تلاش برای پیدا کردن اعداد دیجیتالی (مثل 10000)
    temp_text = text.replace("میلیون", "000000").replace("هزار", "000")
    nums = re.findall(r'\d+', temp_text.replace(',', ''))
    if nums:
        return int(nums[0])
    
    # دوم: تلاش برای تبدیل متن حروفی به عدد (مثل بیست هزار)
    try:
        # حذف کلمات غیر مرتبط برای کمک به کتابخانه مبدل
        clean_text = re.sub(r'[^\u0621-\u064A\u067E\u0686\u0698\u06AF\s]', '', text)
        for word in ["تومان", "تومن", "ریال", "هزینه", "درآمد", "واریز"]:
            clean_text = clean_text.replace(word, "")
        
        converted = persian_w2n.word_to_num(clean_text.strip())
        if converted > 0:
            return converted
    except:
        pass
    
    return None

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
