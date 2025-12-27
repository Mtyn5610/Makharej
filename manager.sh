#!/bin/bash

# مسیر پوشه پروژه
PROJECT_DIR="$HOME/Makharej"

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
    echo "6) ❌ خروج از منو"
    echo -e "\e[31m7) 🧨 پاکسازی کامل پروژه (Uninstall)\e[0m"
    echo "---------------------------------------"
    read -p "انتخاب کنید: " opt

    case $opt in
        1)
            # ابتدا تمام اسکرین‌های قدیمی با نام jibi_bot را می‌بندد
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            # حالا نسخه جدید را اجرا می‌کند
            screen -dmS jibi_bot $PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/bot.py
            echo -e "\e[32m✅ ربات با موفقیت در یک سشن تازه روشن شد.\e[0m"
            ;;
        2)
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            echo -e "\e[31m🛑 تمام سشن‌های ربات متوقف شدند.\e[0m"
            ;;
        3)
            screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
            sleep 1
            screen -dmS jibi_bot $PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/bot.py
            echo -e "\e[36m🔄 ری‌استارت انجام شد.\e[0m"
            ;;
        4)
            # چک می‌کند آیا اسکرینی باز هست یا نه
            if screen -list | grep -q "jibi_bot"; then
                screen -r jibi_bot
            else
                echo -e "\e[31m❌ هیچ رباتی در حال اجرا نیست.\e[0m"
            fi
            ;;
        5)
            zip -r $PROJECT_DIR/backup_$(date +%Y%m%d).zip $PROJECT_DIR/user_*.db
            echo -e "\e[32m✅ فایل بکاپ در پوشه پروژه ساخته شد.\e[0m"
            ;;
        6)
            exit 0
            ;;
        7)
            read -p "⚠️ آیا مطمئن هستید که می‌خواهید کل پروژه را پاک کنید؟ (y/n): " confirm
            if [ "$confirm" == "y" ]; then
                screen -ls | grep "jibi_bot" | cut -d. -f1 | awk '{print $1}' | xargs -r -n1 screen -XS quit
                rm -rf $PROJECT_DIR
                sed -i '/alias JibiNo=/d' ~/.bashrc
                echo -e "\e[31m🔥 پروژه با موفقیت حذف شد.\e[0m"
                exit 0
            fi
            ;;
        *)
            echo "گزینه نامعتبر."
            ;;
    esac
    read -p "برگشت با اینتر..."
done
