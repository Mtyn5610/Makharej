#!/bin/bash
# ۱. پاکسازی پوشه‌های قدیمی
rm -rf Makharej
screen -XS my_bot quit 2>/dev/null

# ۲. دریافت توکن
clear
echo "=========================================="
read -p "🔑 Telegram Bot Token: " user_token
echo "=========================================="

# ۳. نصب ملزومات سیستمی
sudo apt update && sudo apt install -y python3-pip python3-venv screen ffmpeg git

# ۴. دانلود پروژه
git clone https://github.com/Mtyn5610/Makharej.git
cd Makharej

# ۵. ساخت محیط مجازی و نصب پکیج‌ها
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# ۶. تنظیم توکن
sed -i "s/TOKEN = \"ENTER_TOKEN_HERE\"/TOKEN = \"$user_token\"/" bot.py

# ۷. اجرا در پس‌زمینه
screen -dmS my_bot ./venv/bin/python3 bot.py

echo "✅ نصب کامل شد! ربات در حال اجراست."
echo "💡 برای مشاهده وضعیت زنده: screen -r my_bot"
