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
