#!/usr/bin/env python3
import os, sqlite3, re, pandas as pd, jdatetime, requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- تنظیمات سیستمی (توسط install.sh پر می‌شود) ---
TOKEN = "PLACEHOLDER_TOKEN"
ADMIN_ID = 999999999

# --- دیتابیس‌ها ---
def init_dbs():
    conn = sqlite3.connect("main.db")
    # جدول کاربران و اشتراک (status 1 = VIP)
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (uid INTEGER PRIMARY KEY, status INTEGER DEFAULT 0, daily_count INTEGER DEFAULT 0, 
                  last_date DATE, total_paid INTEGER DEFAULT 0)''')
    # جدول پس‌انداز غیرنقدی (مورد ۱۱)
    conn.execute('''CREATE TABLE IF NOT EXISTS savings 
                 (id INTEGER PRIMARY KEY, uid INTEGER, asset_name TEXT, amount REAL, unit TEXT)''')
    conn.commit()
    conn.close()

def get_user_db(uid):
    conn = sqlite3.connect(f"user_{uid}.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tx 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, amount INTEGER, desc TEXT, type TEXT, category TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    return conn

# --- ۱. منطق هوشمند مبالغ (۲ تومن = ۲ میلیون | ۴۶۵۰ تومن = ۴.۶ میلیون) ---
def extract_amount(text):
    # تبدیل حروف به عدد
    word_to_num = {"یک": "1", "دو": "2", "سه": "3", "چهار": "4", "پنج": "5", "شش": "6", "هفت": "7", "هشت": "8", "نه": "9", "ده": "10"}
    processed = text
    for word, num in word_to_num.items():
        processed = processed.replace(word, num)

    processed = processed.replace("میلیون", "000000").replace("ملیون", "000000").replace("هزار", "000")
    nums = "".join(re.findall(r'\d+', processed.replace(',', '')))
    if not nums: return None
    amount = int(nums)
    
    # اصلاح هوشمند واحدها
    if amount < 1000 and "هزار" not in text and "000" not in text:
        amount *= 1000000  # مثال: 2 تومن -> 2,000,000
    elif 1000 <= amount < 10000 and "هزار" not in text:
        amount *= 1000     # مثال: 4650 تومن -> 4,650,000
    
    return amount

# --- ۸. دیکشنری گسترده دسته‌بندی ---
INCOME_KEYWORDS = ["حقوق", "درآمد", "واریز", "فروختم", "سود", "هدیه", "طلب", "کاسبی"]
CATEGORIES = {
    "🍎 تغذیه": ["غذا", "رستوران", "سوپر", "میوه", "نون", "ناهار", "شام"],
    "🚗 حمل و نقل": ["بنزین", "اسنپ", "تپسی", "ماشین", "تعمیر", "کارواش"],
    "🏠 مسکن و قبوض": ["اجاره", "شارژ", "آب", "برق", "گاز", "اینترنت", "بسته"],
    "💊 سلامت": ["دکتر", "دارو", "ویزیت", "بیمارستان", "دندان"],
    "👕 پوشاک و زیبایی": ["لباس", "کفش", "آرایشگاه", "سلمانی", "عطر"],
    "📱 تکنولوژی": ["گوشی", "موبایل", "لپ‌تاپ", "شارژر", "هارد"],
    "💎 پس‌انداز": ["طلا", "دلار", "سکه", "نقره", "تتر"]
}

# --- سیستم محدودیت کاربر رایگان (مورد ۴) ---
async def is_allowed(uid):
    if uid == ADMIN_ID: return True
    conn = sqlite3.connect("main.db")
    user = conn.execute("SELECT status, daily_count, last_date FROM users WHERE uid=?", (uid,)).fetchone()
    today = jdatetime.date.today().isoformat()
    
    if not user:
        conn.execute("INSERT INTO users (uid, last_date) VALUES (?, ?)", (uid, today))
        conn.commit()
        return True
    
    status, count, l_date = user
    if status == 1: return True # VIP نامحدود
    
    if l_date != today:
        conn.execute("UPDATE users SET daily_count=0, last_date=? WHERE uid=?", (today, uid))
        conn.commit()
        count = 0
    
    if count >= 10: return False # سقف ۱۰ تراکنش روزانه رایگان
    
    conn.execute("UPDATE users SET daily_count = daily_count + 1 WHERE uid=?", (uid,))
    conn.commit()
    return True

# --- پنل مدیریت ادمین (مورد ۳، ۵، ۶) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    kb = [
        [InlineKeyboardButton("📢 ارسال همگانی (Broadcast)", callback_data="adm_bc")],
        [InlineKeyboardButton("💎 شارژ/VIP کاربر", callback_data="adm_vip")],
        [InlineKeyboardButton("📊 گزارش سود و آمار کل", callback_data="adm_stats")]
    ]
    await update.message.reply_text("🛠 **پنل مدیریت ارشد جیبی‌نو**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# --- هندلرهای دستورات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_dbs()
    
    # خبر به ادمین برای کاربر جدید
    if uid != ADMIN_ID:
        try: await context.bot.send_message(ADMIN_ID, f"🔔 کاربر جدید: `{uid}`", parse_mode="Markdown")
        except: pass

    kb = [
        ["📊 گزارش و موجودی", "📥 خروجی اکسل"],
        ["✨ لیست پس‌انداز", "🔍 جستجو"],
        ["📞 پشتیبانی", "⚠️ پاکسازی کل"]
    ]
    if uid == ADMIN_ID: kb.append(["🛠 پنل مدیریت ادمین"])
    await update.message.reply_text("🌟 به جیبی‌نو خوش آمدید!", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# --- ۱۰. جستجوی پیشرفته ---
async def search_tx(update: Update, context: ContextTypes.DEFAULT_TYPE, term):
    uid = update.effective_user.id
    conn = get_user_db(uid)
    df = pd.read_sql_query(f"SELECT SUM(amount) as s FROM tx WHERE desc LIKE '%{term}%'", conn)
    val = df['s'].iloc[0] or 0
    await update.message.reply_text(f"🔍 مجموع تراکنش‌ها برای «{term}»:\n💰 {val:,} تومان")

# --- ۱۱. پس‌انداز شیشه‌ای ---
async def show_savings(update: Update):
    uid = update.effective_user.id
    conn = sqlite3.connect("main.db")
    rows = conn.execute("SELECT asset_name, amount, unit FROM savings WHERE uid=?", (uid,)).fetchall()
    if not rows: return await update.message.reply_text("لیست پس‌انداز شما خالی است.")
    text = "💎 **لیست دارایی‌های شما:**\n\n"
    for r in rows: text += f"🔹 {r[0]}: {r[1]} {r[2]}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# --- هندلر دکمه‌های شیشه‌ای ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    if uid != ADMIN_ID: return
    await query.answer()

    if query.data == "adm_stats":
        conn = sqlite3.connect("main.db")
        stats = conn.execute("SELECT COUNT(*), SUM(total_paid) FROM users").fetchone()
        vips = conn.execute("SELECT COUNT(*) FROM users WHERE status=1").fetchone()[0]
        await query.edit_message_text(f"📊 **گزارش کل:**\n👥 کاربران: {stats[0]}\n💎 ویژه: {vips}\n💰 سود کل: {stats[1] or 0:,} ت")
    elif query.data == "adm_bc":
        await query.edit_message_text("📝 متن پیام همگانی را بفرستید:")
        context.user_data['mode'] = 'bc'
    elif query.data == "adm_vip":
        await query.edit_message_text("👤 بفرستید -> `آیدی:مبلغ` (مثال: `1234:50000`)", parse_mode="Markdown")
        context.user_data['mode'] = 'vip'

# --- پردازش پیام‌های اصلی ---
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    mode = context.user_data.get('mode')

    # عملیات ادمین
    if uid == ADMIN_ID and mode in ['bc', 'vip']:
        if mode == 'bc':
            conn = sqlite3.connect("main.db")
            uids = [u[0] for u in conn.execute("SELECT uid FROM users").fetchall()]
            for u in uids:
                try: await context.bot.send_message(u, f"📢 **پیام مدیریت:**\n\n{text}", parse_mode="Markdown")
                except: continue
            await update.message.reply_text("✅ ارسال شد.")
        elif mode == 'vip':
            try:
                target, pay = text.split(':')
                conn = sqlite3.connect("main.db")
                conn.execute("UPDATE users SET status=1, total_paid=total_paid+? WHERE uid=?", (int(pay), target.strip()))
                conn.commit()
                await update.message.reply_text(f"✅ کاربر {target} شارژ شد.")
            except: await update.message.reply_text("❌ خطا در فرمت.")
        context.user_data['mode'] = None; return

    # پشتیبانی (مورد ۷)
    if mode == 'support':
        await context.bot.send_message(ADMIN_ID, f"📩 پیام پشتیبانی از `{uid}`:\n\n{text}", parse_mode="Markdown")
        await update.message.reply_text("✅ ارسال شد."); context.user_data['mode'] = None; return

    # دکمه‌های منو
    if text == "🛠 پنل مدیریت ادمین": await admin_panel(update, context); return
    if text == "✨ لیست پس‌انداز": await show_savings(update); return
    if text == "📞 پشتیبانی": await update.message.reply_text("پیام خود را بنویسید:"); context.user_data['mode'] = 'support'; return
    if "چقدر" in text: await search_tx(update, context, text.split("چقدر")[-1].strip()); return

    # محدودیت رایگان
    if not await is_allowed(uid):
        return await update.message.reply_text("❌ سقف تراکنش روزانه تمام شد. اشتراک تهیه کنید.")

    # ثبت تراکنش و دارایی
    amt = extract_amount(text)
    if amt:
        cat = "📝 سایر"
        for c, words in CATEGORIES.items():
            if any(w in text for w in words): cat = c
        
        # ثبت در پس‌انداز (مورد ۱۱)
        if cat == "💎 پس‌انداز":
            nums = re.findall(r'\d+', text)
            if nums:
                conn = sqlite3.connect("main.db")
                conn.execute("INSERT INTO savings (uid, asset_name, amount, unit) VALUES (?, ?, ?, ?)", (uid, text, nums[0], "واحد"))
                conn.commit()

        # ثبت تراکنش مالی
        is_inc = any(w in text for w in INCOME_KEYWORDS)
        db = get_user_db(uid)
        db.execute("INSERT INTO tx (amount, desc, type, category) VALUES (?, ?, ?, ?)", (amt if is_inc else -amt, text, "درآمد" if is_inc else "هزینه", cat))
        db.commit()
        await update.message.reply_text(f"✅ ثبت شد: {amt:,} تومان\n🗂 دسته: {cat}")

def main():
    init_dbs()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler, pattern="^adm_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("JibiNo Pro is Live!")
    app.run_polling()

if __name__ == '__main__': main()    df = pd.read_sql_query("SELECT date, type, amount, category, desc FROM tx ORDER BY id DESC", conn)
    conn.close()
    if df.empty: return await update.message.reply_text("❌ دیتابیس خالی است.")

    def to_jalali(iso_date):
        try:
            date_part = iso_date.split(' ')[0]
            y, m, d = map(int, date_part.split('-'))
            return jdatetime.date.fromgregorian(day=d, month=m, year=y).strftime("%Y/%m/%d")
        except: return iso_date

    df['تاریخ شمسی'] = df['date'].apply(to_jalali)
    df = df[['تاریخ شمسی', 'type', 'amount', 'category', 'desc']]
    path = f"report_{uid}.xlsx"
    df.to_excel(path, index=False)
    await update.message.reply_document(document=open(path, 'rb'), caption="📊 گزارش اکسل با تاریخ شمسی")
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
        await update.message.reply_text(f"🗑 آخرین تراکنش حذف شد.")
    else:
        await update.message.reply_text("تراکنشی یافت نشد.")
    conn.close()

async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(uid)
    conn.execute("DELETE FROM tx"); conn.commit(); conn.close()
    await update.message.reply_text("⚠️ تمام اطلاعات شما پاک شد.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = await update.message.reply_text("⏳ در حال پردازش صوت...")
    ogg, wav = f"v_{update.effective_user.id}.ogg", f"v_{update.effective_user.id}.wav"
    try:
        f = await context.bot.get_file(update.message.voice.file_id)
        await f.download_to_drive(ogg)
        AudioSegment.from_ogg(ogg).export(wav, format="wav")
        r = sr.Recognizer()
        with sr.AudioFile(wav) as source:
            text = r.recognize_google(r.record(source), language="fa-IR")
        res = await process_data(update.effective_user.id, text)
        await m.edit_text(res)
    except: await m.edit_text("❌ متوجه صدا نشدم.")
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
    print("JibiNo is online...")
    app.run_polling()

if __name__ == '__main__':
    main()
