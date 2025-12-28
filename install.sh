#!/usr/bin/env python3
import os, sqlite3, re, pandas as pd, jdatetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- تنظیمات سیستمی (توسط install.sh پر می‌شود) ---
TOKEN = "PLACEHOLDER_TOKEN"
ADMIN_ID = 999999999

# --- ۱. مدیریت دیتابیس‌ها ---
def init_dbs():
    conn = sqlite3.connect("main.db")
    # جدول کاربران و اشتراک
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (uid INTEGER PRIMARY KEY, status INTEGER DEFAULT 0, daily_count INTEGER DEFAULT 0, 
                  last_date DATE, total_paid INTEGER DEFAULT 0)''')
    # جدول پس‌انداز غیرنقدی
    conn.execute('''CREATE TABLE IF NOT EXISTS savings 
                 (id INTEGER PRIMARY KEY, uid INTEGER, asset_name TEXT, amount REAL, unit TEXT)''')
    conn.commit()
    conn.close()

def get_user_db(uid):
    conn = sqlite3.connect(f"user_{uid}.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS tx 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, amount INTEGER, desc TEXT, 
                  type TEXT, category TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    return conn

# --- ۲. منطق هوشمند استخراج مبلغ و تشخیص درآمد/هزینه ---
def extract_amount(text):
    word_to_num = {"یک": "1", "دو": "2", "سه": "3", "چهار": "4", "پنج": "5", "شش": "6", "هفت": "7", "هشت": "8", "نه": "9", "ده": "10"}
    processed = text
    for word, num in word_to_num.items():
        processed = processed.replace(word, num)

    processed = processed.replace("میلیون", "000000").replace("ملیون", "000000").replace("هزار", "000")
    nums = "".join(re.findall(r'\d+', processed.replace(',', '')))
    if not nums: return None
    amount = int(nums)
    
    # اصلاح هوشمند واحدها (درخواست شما)
    if amount < 1000 and "هزار" not in text and "000" not in text:
        amount *= 1000000 # 2 -> 2,000,000
    elif 1000 <= amount < 10000 and "هزار" not in text:
        amount *= 1000    # 4650 -> 4,650,000
    
    return amount

# --- ۳. دیکشنری‌های گسترده دسته‌بندی ---
INCOME_KEYWORDS = ["حقوق", "درآمد", "واریز", "فروختم", "سود", "هدیه", "طلب", "کاسبی", "یارانه"]
CATEGORIES = {
    "🍎 تغذیه و سوپر": ["غذا", "رستوران", "سوپرمارکت", "نون", "نان", "میوه", "ناهار", "شام", "کافه", "هایپر", "لبنیات"],
    "🚗 حمل و نقل": ["بنزین", "اسنپ", "تپسی", "ماشین", "تعمیر", "کارواش", "مترو", "تاکسی", "لاستیک"],
    "🏠 مسکن و قبوض": ["اجاره", "شارژ", "قبض", "آب", "برق", "گاز", "اینترنت", "تلفن", "بسته", "وای فای"],
    "💊 سلامت و درمان": ["دکتر", "دارو", "ویزیت", "داروخانه", "بیمارستان", "دندانپزشکی", "عینک"],
    "👕 پوشاک و زیبایی": ["لباس", "کفش", "شلوار", "آرایشگاه", "سلمانی", "ادکلن", "عطر", "پوست"],
    "🎮 تفریح و آموزش": ["سینما", "بازی", "سفر", "هتل", "کادو", "کتاب", "کلاس", "شهریه", "دوره"],
    "📱 تکنولوژی": ["موبایل", "گوشی", "شارژر", "لپ‌تاپ", "هدفون", "نرم‌افزار"],
    "💎 پس‌انداز": ["طلا", "دلار", "ارز", "سکه", "تتر", "بیت کوین", "نقره"]
}

# --- ۴. توابع کاربردی و گزارش‌گیری ---
async def get_report(uid):
    conn = get_user_db(uid)
    df = pd.read_sql_query("SELECT amount, category FROM tx", conn)
    if df.empty: return "اطلاعاتی ثبت نشده است."
    
    total = df['amount'].sum()
    expenses = df[df['amount'] < 0].groupby('category')['amount'].sum().abs()
    
    report = f"💰 **موجودی کل:** {total:,} تومان\n\n🔻 **هزینه‌ها به تفکیک:**\n"
    for cat, val in expenses.items():
        report += f"🔸 {cat}: {val:,} تومان\n"
    return report

# --- ۵. هندلرهای تلگرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_dbs()
    
    # ثبت کاربر در دیتابیس مرکزی
    conn = sqlite3.connect("main.db")
    conn.execute("INSERT OR IGNORE INTO users (uid, last_date) VALUES (?, ?)", (uid, jdatetime.date.today().isoformat()))
    conn.commit()

    kb = [
        ["📊 گزارش و موجودی", "📥 خروجی اکسل"],
        ["✨ لیست پس‌انداز", "🔍 جستجو"],
        ["📞 پشتیبانی", "⚠️ پاکسازی کل"]
    ]
    if uid == ADMIN_ID: kb.append(["🛠 پنل مدیریت ادمین"])
    await update.message.reply_text("🌟 به جیبی‌نو پرو خوش آمدید!\nمثال ثبت: «۵۰ تومن بنزین» یا «۲ تومن حقوق»", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    kb = [
        [InlineKeyboardButton("📢 پیام همگانی", callback_data="adm_bc"), InlineKeyboardButton("📊 سود و آمار", callback_data="adm_stats")],
        [InlineKeyboardButton("💎 شارژ/VIP کاربر", callback_data="adm_vip")]
    ]
    await update.message.reply_text("🛠 پنل مدیریت ارشد:", reply_markup=InlineKeyboardMarkup(kb))

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    mode = context.user_data.get('mode')

    # بخش مدیریت و ادمین
    if uid == ADMIN_ID and mode:
        if mode == 'bc':
            conn = sqlite3.connect("main.db")
            uids = [u[0] for u in conn.execute("SELECT uid FROM users").fetchall()]
            for u in uids:
                try: await context.bot.send_message(u, f"📢 **پیام مدیریت:**\n\n{text}")
                except: continue
            await update.message.reply_text("✅ ارسال شد."); context.user_data['mode'] = None; return
        
        elif mode == 'vip':
            try:
                tid, pay = text.split(':')
                conn = sqlite3.connect("main.db")
                conn.execute("UPDATE users SET status=1, total_paid=total_paid+? WHERE uid=?", (int(pay), tid.strip()))
                conn.commit()
                await update.message.reply_text("✅ کاربر ویژه شد."); await context.bot.send_message(tid.strip(), "🎉 حساب شما VIP شد!")
            except: await update.message.reply_text("فرمت اشتباه است.")
            context.user_data['mode'] = None; return

    # دکمه‌های منو
    if text == "📊 گزارش و موجودی": await update.message.reply_text(await get_report(uid), parse_mode="Markdown"); return
    if text == "🛠 پنل مدیریت ادمین": await admin_panel(update, context); return
    if text == "📞 پشتیبانی": await update.message.reply_text("پیام خود را بفرستید:"); context.user_data['mode'] = 'supp'; return
    
    if mode == 'supp':
        await context.bot.send_message(ADMIN_ID, f"📩 پیام از `{uid}`:\n\n{text}"); await update.message.reply_text("ارسال شد."); context.user_data['mode'] = None; return

    # ثبت تراکنش مالی
    amt = extract_amount(text)
    if amt:
        cat = "📝 سایر"
        for c, words in CATEGORIES.items():
            if any(w in text for w in words): cat = c
        
        is_inc = any(w in text for w in INCOME_KEYWORDS)
        
        # ثبت پس‌انداز غیرنقدی
        if cat == "💎 پس‌انداز":
            nums = re.findall(r'\d+', text)
            if nums:
                conn = sqlite3.connect("main.db")
                conn.execute("INSERT INTO savings (uid, asset_name, amount, unit) VALUES (?, ?, ?, ?)", (uid, text, nums[0], "واحد"))
                conn.commit()

        db = get_user_db(uid)
        db.execute("INSERT INTO tx (amount, desc, type, category) VALUES (?, ?, ?, ?)", 
                   (amt if is_inc else -amt, text, "درآمد" if is_inc else "هزینه", cat))
        db.commit()
        await update.message.reply_text(f"✅ {'درآمد' if is_inc else 'هزینه'} ثبت شد: {amt:,} تومان\n🗂 دسته: {cat}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID: return
    await query.answer()
    if query.data == "adm_stats":
        conn = sqlite3.connect("main.db")
        res = conn.execute("SELECT COUNT(*), SUM(total_paid) FROM users").fetchone()
        await query.edit_message_text(f"📊 آمار کل:\n👥 کاربران: {res[0]}\n💰 سود حاصله: {res[1] or 0:,} تومان")
    elif query.data == "adm_bc": await query.edit_message_text("پیام همگانی را بنویسید:"); context.user_data['mode'] = 'bc'
    elif query.data == "adm_vip": await query.edit_message_text("بفرستید -> `آیدی:مبلغ`:"); context.user_data['mode'] = 'vip'

def main():
    init_dbs()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all))
    app.run_polling()

if __name__ == '__main__': main()
