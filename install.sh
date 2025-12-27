#!/bin/bash

# آدرس مخزن شما
REPO_URL="https://raw.githubusercontent.com/Mtyn5610/Makharej/main"

clear
echo "==============================================="
echo "        JibiNo Installer - جیبی‌نو             "
echo "==============================================="

# ۱. دریافت توکن
read -p "Token: " bot_token
if [ -z "$bot_token" ]; then
    echo "خطا: توکن وارد نشد."
    exit 1
fi

# ۲. ایجاد پوشه و دانلود فایل‌ها
mkdir -p ~/Makharej && cd ~/Makharej
curl -sLO "$REPO_URL/bot.py"
curl -sLO "$REPO_URL/requirements.txt"
curl -sLO "$REPO_URL/manager.sh"

# ۳. نصب پیش‌نیازها
sudo apt update -y
sudo apt install -y python3-pip python3-venv ffmpeg screen zip

# ۴. راه‌اندازی پایتون
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# ۵. تزریق توکن به کد
sed -i "s/ENTER_TOKEN_HERE/$bot_token/" bot.py

# ۶. تنظیم دسترسی و میانبر
chmod +x manager.sh
if ! grep -q "alias JibiNo=" ~/.bashrc; then
    echo "alias JibiNo='bash ~/Makharej/manager.sh'" >> ~/.bashrc
fi

echo "✅ نصب با موفقیت تمام شد."
echo "برای شروع بنویسید: JibiNo"
sleep 2

# ۷. اجرای منو
bash ~/Makharej/manager.sh
