#!/bin/bash

# ۱. پاکسازی نسخه قبلی و دریافت فایل‌های جدید
echo "🧹 در حال آماده‌سازی و دریافت فایل‌ها..."
rm -rf Makharej
git clone https://github.com/Mtyn5610/Makharej.git
cd Makharej

# ۲. نصب پیش‌نیازهای سیستم
echo "🔄 در حال نصب پیش‌نیازها..."
sudo apt update && sudo apt install -y python3-pip screen

# ۳. دریافت توکن
echo "------------------------------------------"
read -p "🔑 توکن ربات تلگرام را وارد کنید: " user_token
echo "------------------------------------------"

# ۴. نصب کتابخانه‌ها
echo "📦 در حال نصب کتابخانه‌های پایتون..."
pip install -r requirements.txt

# ۵. جایگذاری توکن در کد
sed -i "s|ENTER_TOKEN_HERE|$user_token|g" bot.py

# ۶. اجرا در حالت Screen
echo "🚀 در حال اجرای ربات در پس‌زمینه..."
screen -dmS my_bot python3 bot.py

echo "✅ نصب با موفقیت به پایان رسید!"
echo "💡 برای دیدن لاگ‌ها: screen -r my_bot"
echo "💡 برای توقف کامل ربات: screen -S my_bot -X quit"
