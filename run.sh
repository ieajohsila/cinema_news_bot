#!/bin/bash

echo "🎬 ربات خبری سینما - اسکریپت راه‌اندازی"
echo "========================================"

# بررسی Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 نصب نیست!"
    exit 1
fi

# بررسی BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    echo "⚠️  هشدار: BOT_TOKEN تنظیم نشده است"
    echo "💡 لطفاً قبل از اجرا تنظیم کنید:"
    echo "   export BOT_TOKEN='YOUR_TOKEN_HERE'"
    exit 1
fi

# نصب requirements
echo "📦 نصب کتابخانه‌ها..."
pip install -r requirements.txt

# مقداردهی اولیه (اختیاری)
echo ""
read -p "❓ آیا می‌خواهید منابع پیش‌فرض را اضافه کنید؟ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 initialize.py
fi

# اجرای ربات
echo ""
echo "🚀 در حال راه‌اندازی ربات..."
python3 main.py
