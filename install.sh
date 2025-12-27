#!/bin/bash
# ۱. دریافت توکن در همان ثانیه اول
clear
echo "------------------------------------------"
read -p "🔑 Telegram Bot Token را وارد کنید: " user_token
echo "------------------------------------------"

# ۲. نصب پیش‌نیازهای سیستم
echo "🔄 در حال نصب پیش‌نیازهای لینوکس..."
sudo apt update && sudo apt install -y python3-pip python3-venv screen ffmpeg git

# ۳. دانلود پروژه
echo "📥 در حال دانلود پروژه از گیت‌هاب..."
git clone https://github.com/Mtyn5610/Makharej.git
cd Makharej

# ۴. ساخت محیط مجازی و نصب کتابخانه‌ها
echo "📦 در حال ساخت محیط مجازی و نصب پکیج‌ها (کمی زمان‌بر)..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install python-telegram-bot pandas openpyxl numpy==1.26.4 openai-whisper

# ۵. جایگذاری هوشمند توکن
echo "⚙️ در حال تنظیم توکن در فایل bot.py..."
sed -i "s/TOKEN = \"ENTER_TOKEN_HERE\"/TOKEN = \"$user_token\"/" bot.py

# ۶. اجرای نهایی در پس‌زمینه
echo "🚀 ربات در حال اجراست..."
screen -dmS my_bot ./venv/bin/python3 bot.py

echo "✅ تمام! حالا می‌توانید به ربات در تلگرام پیام بدهید."
echo "💡 نکته: پردازش اولین ویس ممکن است ۱ دقیقه طول بکشد (به دلیل دانلود مدل هوش مصنوعی)."
