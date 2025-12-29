import re

class TextProcessor:
    def __init__(self):
        # ۱. دیکشنری اعداد و مقادیر حروفی
        self.words_to_num = {
            "نیم": 0.5, "نصف": 0.5, "ربع": 0.25,
            "سه ربع": 0.75, "یک و نیم": 1.5, "دو و نیم": 2.5,
            "یک": 1, "دو": 2, "سه": 3, "چهار": 4, "پنج": 5, "ده": 10
        }
        
        # ۲. دیکشنری کلمات کلیدی برای دسته‌بندی دارایی‌ها
        self.keywords = {
            "gold": [
                "طلا", "آبشده", "مثقال", "۱۸عیار", "750", 
                "انگشتر", "گردنبند", "دستبند", "النگو"
            ],
            "coin": [
                "سکه", "امامی", "بهار آزادی", "نیم‌سکه", "ربع‌سکه", 
                "گرمی", "پارسیان", "پهلوی"
            ],
            "currency": [
                "دلار", "یورو", "تتر", "درهم", "لیر", 
                "پوند", "فرانک", "یوآن", "دینار"
            ]
        }
        
        # نرخ‌های تبدیل ثابت
        self.METHQAL_TO_GRAM = 4.3318
        self.SOOT_TO_GRAM = 0.001

    def extract_data(self, text):
        """استخراج مقدار، واحد و نوع دارایی از متن کاربر"""
        value = None
        
        # پیدا کردن مقدار عددی (حروفی یا رقمی)
        for word, num in self.words_to_num.items():
            if word in text:
                value = num
                break
        
        if value is None:
            numbers = re.findall(r"(\d+(?:\.\d+)?)", text)
            if numbers:
                value = float(numbers[0])

        if value is None:
            return None, None

        # تشخیص نوع دارایی و تبدیل واحدها
        asset_type = "unknown"
        final_value = value

        # بررسی طلا و تبدیل مثقال/سوت به گرم
        if any(word in text for word in self.keywords["gold"] + ["سوت"]):
            asset_type = "gold"
            if "مثقال" in text:
                final_value = value * self.METHQAL_TO_GRAM
            elif "سوت" in text:
                final_value = value * self.SOOT_TO_GRAM
        
        # بررسی ارز و سکه (ذخیره به صورت تعداد)
        elif any(word in text for word in self.keywords["currency"] + self.keywords["coin"] + ["عدد"]):
            asset_type = "asset"

        return round(final_value, 4), asset_type
