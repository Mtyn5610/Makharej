#!/bin/bash

# آدرس مخزن گیت‌هاب شما
REPO_URL="https://raw.githubusercontent.com/Mtyn5610/Makharej/main"

clear
echo -e "\033[0;36m"
echo "  ██╗██╗██████╗ ██╗███╗   ██╗ ██████╗ "
echo "  ██║██║██╔══██╗██║████╗  ██║██╔═══██╗"
echo "  ██║██║██████╔╝██║██╔██╗ ██║██║   ██║"
echo "  ██║██║██╔══██╗██║██║╚██╗██║██║   ██║"
echo "  ╚█████╔╝██████╔╝██║██║ ╚████║╚██████╔╝"
echo "   ╚════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ "
echo -e "\033[1;33m      >>> JibiNo Smart Installer <<< \033[0m"
echo "-----------------------------------------------"

# ۱. دریافت توکن
read -p "لطفاً توکن ربات تلگرام را وارد کنید: " bot_token
if [ -z "$bot_token" ]; then
    echo "خطا: توکن وارد نشد."
    exit 1
fi

# ۲. ایجاد پوشه
mkdir -p ~/Makharej && cd ~/Makharej

# ۳. دانلود فایل‌ها
echo "📥 در حال دریافت فایل‌ها..."
curl -sO "$REPO_URL/bot.py"
curl -sO "$REPO_URL/requirements.txt"
curl -sO "$REPO_URL/manager.sh"

# ۴. نصب پکیج‌ها
echo "📦 در حال نصب پکیج‌های سیستم..."
sudo apt update -y >> /dev/null
sudo apt install -y python3-pip python3-venv ffmpeg screen zip >> /dev/null

# ۵. محیط مجازی و نصب کتابخانه‌ها
python3 -m venv venv
./venv/bin/pip install --upgrade pip >> /dev/null
./venv/bin/pip install -r requirements.txt >> /dev/null

# ۶. تنظیم توکن
sed -i "s/ENTER_TOKEN_HERE/$bot_token/" bot.py

# ۷. تنظیم Alias و دسترسی‌ها
chmod +x manager.sh
if ! grep -q "alias JibiNo=" ~/.bashrc; then
    echo "alias JibiNo='bash ~/Makharej/manager.sh'" >> ~/.bashrc
fi

clear
echo -e "\033[0;32m✅ نصب کامل شد! برای اجرا بنویسید: JibiNo\033[0m"
sleep 2

# ۸. اجرای نهایی
bash ~/Makharej/manager.sh
