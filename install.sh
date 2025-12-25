#!/bin/bash

# ۱. نصب ابزارهای مورد نیاز سیستم
echo "🔄 در حال نصب پیش‌نیازها (Git و Pip)..."
sudo apt update && sudo apt install -y git python3-pip screen

# ۲. دریافت توکن ربات از کاربر
echo "------------------------------------------"
read -p "🔑 لطفاً توکن ربات تلگرام خود را وارد کنید: " user_token
echo "------------------------------------------"

# ۳. نصب کتابخانه‌های پایتون از روی فایل requirements.txt
echo "📦 در حال نصب کتابخانه‌های پایتون..."
pip install -r requirements.txt

# ۴. جایگزینی توکن در فایل bot.py با استفاده از جداکننده | برای امنیت بیشتر
echo "⚙️ در حال پیکربندی نهایی ربات..."
sed -i "s|ENTER_TOKEN_HERE|$user_token|g" bot.py

# ۵. پرسش برای نحوه اجرا
echo "✅ نصب با موفقیت انجام شد!"
echo "❓ می‌خواهید ربات همین الان در حالت پایدار (Screen) اجرا شود؟"
read -p "برای بله عدد 1 و برای خیر عدد 2 را بزنید: " run_choice

if [ "$run_choice" == "1" ]; then
    screen -dmS my_bot python3 bot.py
    echo "🚀 ربات در پس‌زمینه روشن شد."
    echo "💡 برای مشاهده وضعیت ربات دستور مقابل را بزنید: screen -r my_bot"
else
    echo "🆗 بسیار خب. می‌توانید هر زمان خواستید با دستور python3 bot.py ربات را اجرا کنید."
fi
