#!/bin/bash
rm -rf Makharej
git clone https://github.com/Mtyn5610/Makharej.git
cd Makharej

# نصب ابزار پردازش صوت FFmpeg
sudo apt update && sudo apt install -y python3-pip python3-venv screen ffmpeg

read -p "🔑 توکن ربات تلگرام را وارد کنید: " user_token

python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

sed -i "s/TOKEN = \"ENTER_TOKEN_HERE\"/TOKEN = \"$user_token\"/" bot.py

echo "🚀 در حال اجرای ربات (بارگذاری مدل هوش مصنوعی ممکن است ۱ دقیقه طول بکشد)..."
screen -dmS my_bot ./venv/bin/python3 bot.py
echo "✅ نصب با موفقیت انجام شد!"
