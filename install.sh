#!/usr/bin/env python3
# مسیر مخزن شما
REPO_URL="https://raw.githubusercontent.com/Mtyn5610/Makharej/main"

# رنگ‌ها برای خوشگل‌سازی
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

clear
# لوگوی ابتدایی
echo -e "${CYAN}"
echo "  ██╗██╗██████╗ ██╗███╗   ██╗ ██████╗ "
echo "  ██║██║██╔══██╗██║████╗  ██║██╔═══██╗"
echo "  ██║██║██████╔╝██║██╔██╗ ██║██║   ██║"
echo "  ██║██║██╔══██╗██║██║╚██╗██║██║   ██║"
echo "  ╚█████╔╝██████╔╝██║██║ ╚████║╚██████╔╝"
echo "   ╚════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ "
echo -e "${YELLOW}      >>> JibiNo Smart Accountant <<<${NC}"
echo "-----------------------------------------------"

# ۱. دریافت توکن با افکت رنگی
echo -e "${GREEN}[?]${NC} برای شروع، توکن ربات تلگرام را وارد کنید:"
read -p "Token: " bot_token

if [ -z "$bot_token" ]; then
    echo -e "${RED}❌ خطا: توکن وارد نشد. نصب متوقف شد.${NC}"
    exit 1
fi

# ۲. ایجاد پوشه و دانلود (با اطلاع‌رسانی)
echo -e "\n${CYAN}🚀 در حال آماده‌سازی زیرساخت...${NC}"
mkdir -p ~/Makharej && cd ~/Makharej

echo -e "${YELLOW}📥 در حال دریافت فایل‌های هسته...${NC}"
curl -sO "$REPO_URL/bot.py"
curl -sO "$REPO_URL/requirements.txt"
curl -sO "$REPO_URL/manager.sh"

# ۳. نصب پکیج‌های سیستم
echo -e "${CYAN}📦 در حال نصب پکیج‌های لینوکس (ممکن است طول بکشد)...${NC}"
sudo apt update -y >> /dev/null
sudo apt install -y python3-pip python3-venv ffmpeg screen zip >> /dev/null

# ۴. محیط مجازی و پایتون
echo -e "${CYAN}🐍 در حال پیکربندی محیط پایتون...${NC}"
python3 -m venv venv
./venv/bin/pip install --upgrade pip >> /dev/null

echo -e "${YELLOW}📚 در حال نصب کتابخانه‌های هوش مصنوعی...${NC}"
if [ -f "requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt >> /dev/null
else
    ./venv/bin/pip install python-telegram-bot pandas openpyxl SpeechRecognition pydub >> /dev/null
fi

# ۵. تزریق توکن و تنظیم Alias
sed -i "s/ENTER_TOKEN_HERE/$bot_token/" bot.py
if ! grep -q "alias JibiNo=" ~/.bashrc; then
    echo "alias JibiNo='bash ~/Makharej/manager.sh'" >> ~/.bashrc
fi

# ۶. پایان نصب با پیام موفقیت
chmod +x manager.sh
clear
echo -e "${GREEN}"
echo "***********************************************"
echo "* نصب جیبی‌نو با موفقیت انجام شد!       *"
echo "***********************************************"
echo -e "${NC}"
echo -e "🔹 برای مدیریت ربات کافیست دستور ${YELLOW}JibiNo${NC} را تایپ کنید."
echo -e "🔹 ربات شما آماده دریافت اولین ویس یا متن است."
echo -e "\n${CYAN}در حال انتقال به منوی مدیریت...${NC}"
sleep 3

bash ~/Makharej/manager.sh
