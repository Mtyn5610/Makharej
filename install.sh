#!/bin/bash

clear
echo -e "\e[32m"
echo "###############################################"
echo "#        JibiNo - Intelligent Accountant      #"
echo "#            نصب‌کننده خودکار جیبی‌نو            #"
echo "###############################################"
echo -e "\e[0m"

read -p "لطفاً توکن ربات تلگرام را وارد کنید: " bot_token

# ۱. نصب پیش‌نیازها
echo "📦 در حال نصب پکیج‌های مورد نیاز..."
sudo apt update && sudo apt install -y python3-pip python3-venv ffmpeg screen zip >> /dev/null

# ۲. ایجاد محیط کاربری
mkdir -p ~/Makharej && cd ~/Makharej
python3 -m venv venv
./venv/bin/pip install --upgrade pip >> /dev/null
./venv/bin/pip install python-telegram-bot pandas openpyxl SpeechRecognition pydub >> /dev/null

# ۳. تنظیم توکن
sed -i "s/ENTER_TOKEN_HERE/$bot_token/" bot.py

# ۴. ساخت دستور JibiNo در سیستم
if ! grep -q "alias JibiNo=" ~/.bashrc; then
    echo "alias JibiNo='~/Makharej/manager.sh'" >> ~/.bashrc
fi

# ۵. ساخت فایل مدیریت
cat << 'EOF' > ~/Makharej/manager.sh
#!/bin/bash
while true; do
    clear
    echo -e "\e[32m"
    echo "      ██╗██╗██████╗ ██╗███╗   ██╗ ██████╗ "
    echo "      ██║██║██╔══██╗██║████╗  ██║██╔═══██╗"
    echo "      ██║██║██████╔╝██║██╔██╗ ██║██║   ██║"
    echo " ██   ██║██║██╔══██╗██║██║╚██╗██║██║   ██║"
    echo " ╚█████╔╝██║██████╔╝██║██║ ╚████║╚██████╔╝"
    echo "  ╚════╝ ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ "
    echo -e "\e[0m"
    echo "======================================="
    echo "       🌟 منوی مدیریت جـیـبی‌نـو 🌟       "
    echo "======================================="
    echo "1) 🚀 روشن کردن (Start)"
    echo "2) 🛑 خاموش کردن (Stop)"
    echo "3) 🔄 ری‌استارت (Restart)"
    echo "4) 📊 لاگ‌های زنده (Logs)"
    echo "5) 💾 بکاپ دیتابیس (Backup)"
    echo "6) ❌ خروج"
    echo "---------------------------------------"
    read -p "انتخاب کنید: " opt
    case $opt in
        1) screen -dmS jibi_bot ~/Makharej/venv/bin/python3 ~/Makharej/bot.py && echo "✅ روشن شد." ;;
        2) screen -XS jibi_bot quit && echo "🛑 خاموش شد." ;;
        3) screen -XS jibi_bot quit && screen -dmS jibi_bot ~/Makharej/venv/bin/python3 ~/Makharej/bot.py && echo "🔄 ری‌استارت شد." ;;
        4) screen -r jibi_bot ;;
        5) zip -r backup_$(date +%Y%m%d).zip ~/Makharej/user_*.db && echo "✅ بکاپ گرفته شد." ;;
        6) exit 0 ;;
    esac
    read -p "برگشت با اینتر..."
done
EOF
chmod +x ~/Makharej/manager.sh

echo -e "\e[32m✅ نصب کامل شد! برای مدیریت بنویسید: JibiNo\e[0m"
source ~/.bashrc 2>/dev/null
~/Makharej/manager.sh
