import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode

TOKEN = os.getenv("TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    status TEXT
)
""")
conn.commit()

def get_status(user_id):
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def set_status(user_id, status):
    cursor.execute("INSERT OR REPLACE INTO users (user_id, status) VALUES (?, ?)", (user_id, status))
    conn.commit()

@dp.message(Command("start"))
async def start_handler(message: Message):
    status = get_status(message.from_user.id)
    if status == "approved":
        await message.answer("✅ Siz verifikatsiyadan o'tgansiz.")
    else:
        await message.answer("🎥 Iltimos 10-15 soniyalik video yuboring.")

@dp.message(F.video)
async def video_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
        ]
    ])

    await bot.send_video(
        ADMIN_GROUP_ID,
        message.video.file_id,
        caption=f"👤 ID: {message.from_user.id}",
        reply_markup=keyboard
    )

    set_status(message.from_user.id, "pending")
    await message.answer("⏳ Tekshiruvga yuborildi.")

@dp.callback_query(F.data.startswith("approve_"))
async def approve_handler(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    set_status(user_id, "approved")
    await bot.send_message(user_id, "🎉 Siz tasdiqlandingiz.")
    await callback.answer("Tasdiqlandi")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_handler(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    set_status(user_id, "rejected")
    await bot.send_message(user_id, "❌ Video rad etildi. Qayta yuboring.")
    await callback.answer("Rad etildi")

async def main():
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
