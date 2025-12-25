#!/bin/bash

# ۱. پاکسازی کامل
echo "🧹 Cleaning up..."
rm -rf Makharej
screen -XS my_bot quit 2>/dev/null

# ۲. دانلود پروژه
echo "📥 Downloading project..."
git clone https://github.com/Mtyn5610/Makharej.git
cd Makharej || exit

# ۳. نصب پیش‌نیازهای ضروری لینوکس
echo "🔄 Installing system requirements..."
sudo apt update
sudo apt install -y python3-pip python3-venv screen

# ۴. ساخت محیط مجازی (با بررسی خطا)
echo "📦 Creating Virtual Environment..."
python3 -m venv venv
if [ ! -d "venv" ]; then
    echo "❌ Error: Failed to create venv. Installing venv package again..."
    sudo apt install -y python3.12-venv # یا نسخه پایتون خودتان
    python3 -m venv venv
fi

# ۵. نصب کتابخانه‌ها
echo "🐍 Installing Python libraries..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# ۶. تنظیم توکن
echo "------------------------------------------"
read -p "🔑 Telegram Bot Token: " user_token
sed -i "s|ENTER_TOKEN_HERE|$user_token|g" bot.py
echo "------------------------------------------"

# ۷. اجرا
echo "🚀 Starting Bot..."
screen -dmS my_bot ./venv/bin/python3 bot.py

echo "✅ Done! Use 'screen -r my_bot' to see logs."
