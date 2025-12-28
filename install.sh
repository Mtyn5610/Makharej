#!/bin/bash

# مسیر پوشه پروژه
PROJECT_DIR="$HOME/Makharej"
BOT_FILE="$PROJECT_DIR/bot.py"

# --- فاز ۱: نصب پیش‌نیازها و تنظیمات اولیه (فقط در اولین اجرا) ---
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "\e[34m------------------------------------------\e[0m"
    echo -e "\e[1;32m   به نصب‌کننده خودکار جیبی‌نو خوش آمدید   \e[0m"
    echo -e "\e[34m------------------------------------------\e[0m"
    
    # نصب ابزارهای سیستم در صورت نبودن
    sudo apt update && sudo apt install -y python3-venv python3-pip screen zip
    
    # ایجاد محیط مجازی
    python3 -m venv "$PROJECT_DIR/venv"
    "$PROJECT_DIR/venv/bin/pip" install python-telegram-bot pandas jdatetime openpyxl requests flask
    
    # دریافت اطلاعات حساس
    read -p "📌 توکن ربات تلگرام را وارد کنید: " BOT_TOKEN
    read -p "📌 آیدی عددی ادمین اصلی (خودتان) را وارد کنید: " ADMIN_ID

    # تزریق اطلاعات به فایل bot.py
    sed -i "s/PLACEHOLDER_TOKEN/$BOT_TOKEN/g" "$BOT_FILE"
    sed -i "s/999999999/$ADMIN_ID/g" "$BOT_FILE"
    
    echo -e "\e[32m✅ تنظیمات اولیه با موفقیت انجام شد.\e[0m"
    sleep 2
fi

# --- فاز ۲: منوی گرافیکی و مدیریتی جیبی‌نو ---
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
    echo "6) 🔄 آپدیت سورس (Git Pull)"
    echo "7) ❌ خروج از منو"
    echo -e "\e[31m8) 🧨 پاکسازی کامل پروژه (Uninstall)\e[0m"
    echo "---------------------------------------"
    read -p "انتخاب کنید: " opt

    case $opt in
        1)
            # بستن سشن‌های قدیمی
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            # اجرای ربات در سکرین جدید
            screen -dmS jibi_bot "$PROJECT_DIR/venv/bin/python3" "$BOT_FILE"
            echo -e "\e[32m✅ ربات با موفقیت روشن شد.\e[0m"
            ;;
        2)
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            echo -e "\e[31m🛑 ربات متوقف شد.\e[0m"
            ;;
        3)
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            sleep 1
            screen -dmS jibi_bot "$PROJECT_DIR/venv/bin/python3" "$BOT_FILE"
            echo -e "\e[36m🔄 ری‌استارت انجام شد.\e[0m"
            ;;
        4)
            if screen -list | grep -q "jibi_bot"; then
                screen -r jibi_bot
            else
                echo -e "\e[31m❌ هیچ رباتی در حال اجرا نیست.\e[0m"
            fi
            ;;
        5)
            zip -r "$PROJECT_DIR/backup_$(date +%Y%m%d).zip" "$PROJECT_DIR"/*.db
            echo -e "\e[32m✅ بکاپ از تمام دیتابیس‌ها در پوشه پروژه ساخته شد.\e[0m"
            ;;
        6)
            echo "🔄 در حال دریافت آپدیت از گیت‌هاب..."
            cd "$PROJECT_DIR" && git pull origin main
            echo "✅ آپدیت شد. لطفاً یک بار ربات را ری‌استارت (گزینه ۳) کنید."
            ;;
        7)
            exit 0
            ;;
        8)
            read -p "⚠️ آیا مطمئن هستید که می‌خواهید کل پروژه و دیتابیس‌ها را پاک کنید؟ (y/n): " confirm
            if [ "$confirm" == "y" ]; then
                screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
                rm -rf "$PROJECT_DIR"
                echo -e "\e[31m🔥 کل پروژه حذف شد.\e[0m"
                exit 0
            fi
            ;;
        *)
            echo "گزینه نامعتبر."
            ;;
    esac
    read -p "برای بازگشت اینتر بزنید..."
done
