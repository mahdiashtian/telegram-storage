from pyrogram.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton)

start_btn = ReplyKeyboardMarkup(
    [
        ["🗑 حذف فایل", "🗳 آپلود فایل"],
        ["🗞 حذف کپشن", "📝 تنظیم کپشن"],
        ["🗝 حذف پسورد", "🔐 تنظیم پسورد"],
        ["📂 تاریخچه اپلود", "🗂 کد پیگیری فایل"],
        ["🎫 حساب کاربری"],
        ["🛠 سازنده"]
    ], resize_keyboard=True
)

back_btn = ReplyKeyboardMarkup(
    [["🔙 بازگشت"]], resize_keyboard=True
)

admin_btn = ReplyKeyboardMarkup(
    [
        ["🎯 عضویت اجباری"],
        ["📭 فوروارد همگانی", "📬 پیام همگانی"],
        ["❌ حذف ادمین", "👥 نمایش لیست ادمین ها", "👤 افزودن ادمین"],
        ["📈آمار", "🔌بک آپ"]
    ], resize_keyboard=True
)

join_btn = ReplyKeyboardMarkup(
    [
        ["▪️ حذف کانال", "▫️ اضافه کردن کانال"],
        ["🔸 لیست کانال ها"]
    ], resize_keyboard=True
)

channel_join_btn = lambda x, y:  InlineKeyboardButton(f"{x}", url=f"{y}")
