#!/bin/bash
# ۱. دریافت توکن در همان ابتدا
read -p "🔑 توکن ربات را وارد کنید: " user_token

# ۲. نصب پیش‌نیازها
sudo apt update && sudo apt install -y python3-pip python3-venv screen ffmpeg

# ۳. دانلود و ورود
git clone https://github.com/Mtyn5610/Makharej.git
cd Makharej

# ۴. ساخت محیط مجازی و نصب پکیج‌ها
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install python-telegram-bot pandas openpyxl numpy==1.26.4 openai-whisper

# ۵. ست کردن توکن
sed -i "s/TOKEN = \"ENTER_TOKEN_HERE\"/TOKEN = \"$user_token\"/" bot.py

# ۶. اجرا
screen -dmS my_bot ./venv/bin/python3 bot.py
echo "✅ نصب انجام شد. ربات در حال بالا آمدن است..."
