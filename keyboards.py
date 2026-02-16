from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino kodini kiritish")],
            [KeyboardButton(text="ℹ️ Yordam")]
        ],
        resize_keyboard=True
    )

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kino qo‘shish", callback_data="admin:add_movie")],
        [InlineKeyboardButton(text="🗑 Kino o‘chirish", callback_data="admin:del_movie")],
        [InlineKeyboardButton(text="📌 Kanal qo‘shish", callback_data="admin:add_channel")],
        [InlineKeyboardButton(text="❌ Kanal o‘chirish", callback_data="admin:del_channel")],
        [InlineKeyboardButton(text="🧹 Kanallarni tozalash", callback_data="admin:clear_channels")],
        [InlineKeyboardButton(text="📢 Reklama qo‘shish", callback_data="admin:add_ad")],
        [InlineKeyboardButton(text="🗑 Reklamani o‘chirish", callback_data="admin:del_ad")],
        [InlineKeyboardButton(text="🚀 Reklamani yuborish", callback_data="admin:broadcast_ads")],
    ])

def join_channels_kb(channels: list[tuple]):
    # channels: (id, chat_id, username, title)
    rows = []
    for _, _, username, title in channels:
        if username:
            url = f"https://t.me/{username.lstrip('@')}"
            btn_text = f"➕ {title or '@'+username}"
            rows.append([InlineKeyboardButton(text=btn_text, url=url)])
    rows.append([InlineKeyboardButton(text="✅ A’zo bo‘ldim", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
