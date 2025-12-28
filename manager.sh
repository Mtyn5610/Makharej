#!/bin/bash

# مسیر پوشه پروژه
PROJECT_DIR="$HOME/Makharej"
BOT_FILE="$PROJECT_DIR/bot.py"

# تابع نمایش منو
show_menu() {
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
    echo "---------------------------------------"
}

while true; do
    show_menu
    read -p "انتخاب کنید: " opt

    case $opt in
        1)
            # بستن سشن‌های احتمالی قبلی برای جلوگیری از تداخل
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            # اجرا در محیط مجازی
            screen -dmS jibi_bot "$PROJECT_DIR/venv/bin/python3" "$BOT_FILE"
            echo -e "\e[32m✅ ربات در پس‌زمینه (Screen) روشن شد.\e[0m"
            ;;
        2)
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            echo -e "\e[31m🛑 ربات با موفقیت خاموش شد.\e[0m"
            ;;
        3)
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            sleep 1
            screen -dmS jibi_bot "$PROJECT_DIR/venv/bin/python3" "$BOT_FILE"
            echo -e "\e[36m🔄 ری‌استارت انجام شد.\e[0m"
            ;;
        4)
            if screen -list | grep -q "jibi_bot"; then
                echo -e "\e[33mTip: برای خارج شدن از لاگ بدون خاموش شدن ربات، کلید Ctrl+A و سپس D را بزنید.\e[0m"
                sleep 2
                screen -r jibi_bot
            else
                echo -e "\e[31m❌ ربات در حال اجرا نیست.\e[0m"
            fi
            ;;
        5)
            zip -r "$PROJECT_DIR/backup_$(date +%Y%m%d_%H%M).zip" "$PROJECT_DIR"/*.db
            echo -e "\e[32m✅ بکاپ در مسیر $PROJECT_DIR ذخیره شد.\e[0m"
            ;;
        6)
            echo "🔄 در حال دریافت کدهای جدید..."
            cd "$PROJECT_DIR" && git pull origin main
            echo "✅ آپدیت انجام شد. برای اعمال تغییرات، گزینه ۳ (Restart) را بزنید."
            ;;
        7)
            echo "خداحافظ!"
            exit 0
            ;;
        *)
            echo "گزینه نامعتبر است."
            ;;
    esac
    read -p "برای بازگشت به منو اینتر بزنید..."
done
