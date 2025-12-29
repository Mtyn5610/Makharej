import re

class TextProcessor:
    def __init__(self):
        self.words_to_num = {
            "نیم": 0.5, "نصف": 0.5, "ربع": 0.25,
            "سه ربع": 0.75, "یک و نیم": 1.5, "دو و نیم": 2.5
        }
        
    def extract_data(self, text):
        # پیدا کردن مقدار عددی
        value = None
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

        # منطق تبدیل واحد و استانداردسازی
        if "سوت" in text:
            # تبدیل سوت به گرم برای ذخیره استاندارد
            final_value = value / 1000 
            unit = "gram" 
        elif "گرم" in text:
            final_value = value
            unit = "gram"
        else:
            final_value = value
            unit = "unknown"

        return final_value, unit
