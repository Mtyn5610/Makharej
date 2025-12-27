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
    echo "6) ❌ خروج از منو"
    echo -e "\e[31m7) 🧨 پاکسازی کامل پروژه (Uninstall)\e[0m"
    echo "---------------------------------------"
    read -p "انتخاب کنید: " opt
    case $opt in
        1) screen -dmS jibi_bot ~/Makharej/venv/bin/python3 ~/Makharej/bot.py && echo "✅ روشن شد." ;;
        2) screen -XS jibi_bot quit && echo "🛑 خاموش شد." ;;
        3) screen -XS jibi_bot quit && screen -dmS jibi_bot ~/Makharej/venv/bin/python3 ~/Makharej/bot.py && echo "🔄 ری‌استارت شد." ;;
        4) screen -r jibi_bot ;;
        5) zip -r backup_$(date +%Y%m%d).zip ~/Makharej/user_*.db && echo "✅ بکاپ گرفته شد." ;;
        6) exit 0 ;;
        7) 
            read -p "⚠️ آیا مطمئن هستید که می‌خواهید کل پروژه و دیتابیس‌ها را پاک کنید؟ (y/n): " confirm
            if [ "$confirm" == "y" ]; then
                screen -XS jibi_bot quit 2>/dev/null
                rm -rf ~/Makharej
                sed -i '/alias JibiNo=/d' ~/.bashrc
                echo -e "\e[31m🔥 پروژه و تنظیمات کاملاً پاک شدند.\e[0m"
                echo "برای اعمال تغییرات نهایی، دستور 'source ~/.bashrc' را بزنید یا ترمینال را ببندید."
                exit 0
            fi
            ;;
    esac
    read -p "برگشت با اینتر..."
done
