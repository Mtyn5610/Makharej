import os, sqlite3, pandas as pd, re, whisper
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "ENTER_TOKEN_HERE"
# مدل سبک برای سرعت بالا در تشخیص ویس فارسی
model = whisper.load_model("tiny")

def get_db(user_id):
    conn = sqlite3.connect(f"user_{user_id}.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tx 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      amount INTEGER, desc TEXT, type TEXT)''')
    return conn

def extract_amount(text):
    # تبدیل برخی کلمات رایج فارسی به عدد (ساده شده)
    text = text.replace("میلیون", "000000").replace("هزار", "000")
    nums = re.findall(r'\d+', text.replace(',', ''))
    return int(nums[0]) if nums else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["📊 گزارش کلی", "📥 دریافت فایل اکسل"]]
    await update.message.reply_text("سلام! مبلغ را بنویس یا ویس بفرست (مثلاً: ۵۰ هزار تومان واریز حقوق یا ۱۰۰۰۰ بنزین)", 
                                  reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def process_data(user_id, text):
    amount = extract_amount(text)
    if not amount:
        return "❌ متوجه مبلغ نشدم. لطفاً عدد را واضح بگویید یا بنویسید."
    
    tx_type = "درآمد ➕" if any(w in text for w in ["حقوق", "درآمد", "واریز", "فروش"]) else "هزینه ➖"
    val = amount if tx_type == "درآمد ➕" else -amount

    conn = get_db(user_id)
    conn.execute("INSERT INTO tx (amount, desc, type) VALUES (?, ?, ?)", (val, text, tx_type))
    conn.commit()
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
