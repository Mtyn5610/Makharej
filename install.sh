#!/bin/bash

clear
echo "==============================================="
echo "   نصب‌کننده خودکار جیبی‌نو (نسخه اصلاح شده)   "
echo "==============================================="

# ۱. دریافت توکن (مطمئن می‌شویم که متغیر خالی نباشد)
while [ -z "$bot_token" ]; do
    read -p "لطفاً توکن ربات تلگرام را وارد کنید: " bot_token
done

# ۲. ایجاد پوشه پروژه
mkdir -p ~/Makharej && cd ~/Makharej

# ۳. نصب پیش‌نیازها
echo "⏳ در حال نصب پکیج‌های سیستم..."
sudo apt update && sudo apt install -y python3-pip python3-venv ffmpeg screen zip >> /dev/null

# ۴. ساخت محیط مجازی و نصب کتابخانه‌ها
echo "⏳ در حال آماده‌سازی پایتون..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip >> /dev/null
# نصب مستقیم برای اطمینان از عدم وابستگی به فایل خارجی در لحظه نصب
./venv/bin/pip install python-telegram-bot pandas openpyxl SpeechRecognition pydub >> /dev/null

# ۵. تزریق توکن به فایل bot.py
# این دستور مستقیماً کلمه ENTER_TOKEN_HERE را با توکن واقعی جایگزین می‌کند
if [ -f "bot.py" ]; then
    sed -i "s/ENTER_TOKEN_HERE/$bot_token/" bot.py
    echo "✅ توکن با موفقیت در کد ثبت شد."
else
    echo "❌ خطا: فایل bot.py پیدا نشد! مطمئن شوید فایل کنار install.sh است."
    exit 1
fi

# ۶. ثبت دستور JibiNo در سیستم
if ! grep -q "alias JibiNo=" ~/.bashrc; then
    echo "alias JibiNo='~/Makharej/manager.sh'" >> ~/.bashrc
    source ~/.bashrc 2>/dev/null
fi

# ۷. اتمام نصب
clear
echo -e "\e[32m✅ نصب با موفقیت تمام شد!\e[0m"
echo "------------------------------------------------"
echo "برای ورود به منوی مدیریت، دستور زیر را تایپ کنید:"
echo -e "\e[33mJibiNo\e[0m"
echo "(اگر دستور کار نکرد، یکبار ترمینال را ببندید و باز کنید)"
echo "------------------------------------------------"

# اجرای منو برای اولین بار بدون لوپ
chmod +x manager.sh
./manager.sh
