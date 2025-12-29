import os

def setup():
    print("🌟 به نصب‌کننده خودکار جی‌بینو خوش آمدید 🌟")
    
    # دریافت اطلاعات از کاربر
    token = input("لطفاً توکن ربات تلگرام خود را وارد کنید: ")
    admin_id = input("لطفاً آیدی عددی ادمین را وارد کنید: ")
    
    # ساخت فایل .env
    with open(".env", "w") as f:
        f.write(f"BOT_TOKEN={token}\n")
        f.write(f"ADMIN_ID={admin_id}\n")
    
    print("\n✅ فایل تنظیمات (.env) با موفقیت ساخته شد.")
    print("📦 در حال نصب کتابخانه‌های مورد نیاز...")
    
    # نصب کتابخانه‌ها
    os.system("pip install -r requirements.txt")
    
    print("\n🚀 نصب با موفقیت تمام شد! حالا می‌توانید با دستور 'python main.py' ربات را روشن کنید.")

if __name__ == "__main__":
    setup()    uid = update.effective_user.id
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
