import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from db import DB
from keyboards import main_menu, admin_menu, join_channels_kb
from utils import is_admin, check_user_subscriptions

# ✅ .env har doim topilsin (PyCharm/Railway farqi yo‘q)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMINS = set(int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip().isdigit())
DB_PATH = os.getenv("DB_PATH", "bot.db")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN yo‘q. .env yoki Railway Variables’da qo‘ying.")

db = DB(DB_PATH)

# Admin “state”
admin_wait = {}  # user_id -> step dict

def clear_admin_state(user_id: int):
    admin_wait.pop(user_id, None)

async def send_movie(bot: Bot, chat_id: int, movie_row):
    _, code, title, file_id, file_type = movie_row
    caption = f"🎬 <b>{title}</b>\n🔑 Kod: <code>{code}</code>"

    if file_type == "video":
        await bot.send_video(chat_id, file_id, caption=caption, parse_mode="HTML")
    elif file_type == "document":
        await bot.send_document(chat_id, file_id, caption=caption, parse_mode="HTML")
    else:
        await bot.send_message(chat_id, f"{caption}\n\n⚠️ Fayl turi noma’lum.", parse_mode="HTML")

async def require_subscribe(bot: Bot, user_id: int):
    channels = await db.list_channels()
    if not channels:
        return True, None

    ok = await check_user_subscriptions(bot, user_id, channels)
    if ok:
        return True, None

    kb = join_channels_kb(channels)
    return False, kb

def help_text():
    return (
        "📌 Bot ishlashi uchun avval majburiy kanal(lar)ga a’zo bo‘ling.\n"
        "🎬 Keyin kino kodini yuboring — bot kinoni chiqarib beradi.\n"
        "Agar muammo bo‘lsa: @LOGO_55 ga murojaat qiling."
    )

async def main():
    await db.init()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(m: Message):
        # ✅ FIX: /start bosilsa admin state tozalanadi (kino kodi kanalga aylanib qolmaydi)
        clear_admin_state(m.from_user.id)

        await db.add_user(m.from_user.id)

        ok, kb = await require_subscribe(bot, m.from_user.id)
        if not ok:
            await m.answer("❗ Botdan foydalanish uchun quyidagi kanal(lar)ga a’zo bo‘ling:", reply_markup=kb)
            return

        await m.answer("🎬 Kino kodini yuboring yoki pastdagi tugmalardan foydalaning.", reply_markup=main_menu())

    @dp.message(Command("admin"))
    async def admin_cmd(m: Message):
        # ✅ FIX: /admin bosilsa ham state tozalanadi
        clear_admin_state(m.from_user.id)

        if not await is_admin(m.from_user.id, ADMINS):
            return await m.answer("❌ Siz admin emassiz.")
        await m.answer("🛠 Admin panel:\n❌ Bekor qilish: /cancel", reply_markup=admin_menu())

    @dp.message(Command("cancel"))
    async def cancel_cmd(m: Message):
        if await is_admin(m.from_user.id, ADMINS):
            clear_admin_state(m.from_user.id)
            await m.answer("✅ Bekor qilindi. /admin orqali davom eting.")
        else:
            await m.answer("✅ Bekor qilindi.")

    @dp.callback_query(F.data == "check_sub")
    async def check_sub(c: CallbackQuery):
        ok, kb = await require_subscribe(bot, c.from_user.id)
        if ok:
            await c.message.answer("✅ A’zo bo‘ldingiz. Endi kino kodini yuboring.", reply_markup=main_menu())
            await c.answer()
        else:
            await c.message.answer("❌ Hali hamma kanalga a’zo bo‘lmagansiz.", reply_markup=kb)
            await c.answer()

    @dp.message(F.text == "ℹ️ Yordam")
    async def help_btn(m: Message):
        await m.answer(help_text())

    @dp.message(F.text == "🎬 Kino kodini kiritish")
    async def ask_code(m: Message):
        await m.answer("🔑 Kino kodini yuboring (masalan: 123 yoki ABC123).")

    # ================= ADMIN CALLBACKS =================
    @dp.callback_query(F.data.startswith("admin:"))
    async def admin_actions(c: CallbackQuery):
        if not await is_admin(c.from_user.id, ADMINS):
            return await c.answer("Admin emassiz!", show_alert=True)

        action = c.data.split(":", 1)[1]
        uid = c.from_user.id

        if action == "add_movie":
            admin_wait[uid] = {"mode": "add_movie", "step": 1}
            await c.message.answer(
                "➕ <b>Kino qo‘shish</b>\n"
                "1) Kino <b>kodi</b>ni yuboring (unique).\n"
                "❌ Bekor qilish: /cancel",
                parse_mode="HTML"
            )
            return await c.answer()

        if action == "del_movie":
            movies = await db.list_movies(30)
            if not movies:
                await c.message.answer("Kinolar yo‘q.")
                return await c.answer()
            text = "🗑 <b>O‘chirish uchun kino ID</b> yuboring:\n\n" + "\n".join(
                [f"ID: <code>{mid}</code> | <code>{code}</code> — {title}" for mid, code, title in movies]
            ) + "\n\n❌ Bekor qilish: /cancel"
            admin_wait[uid] = {"mode": "del_movie", "step": 1}
            await c.message.answer(text, parse_mode="HTML")
            return await c.answer()

        if action == "add_channel":
            admin_wait[uid] = {"mode": "add_channel", "step": 1}
            await c.message.answer(
                "📌 <b>Kanal qo‘shish</b>\n"
                "Kanal @username ni yuboring (masalan: @mychannel).\n"
                "⚠️ Bot o‘sha kanalda admin bo‘lishi kerak.\n"
                "❌ Bekor qilish: /cancel",
                parse_mode="HTML"
            )
            return await c.answer()

        if action == "del_channel":
            channels = await db.list_channels()
            if not channels:
                await c.message.answer("Kanallar yo‘q.")
                return await c.answer()
            text = "❌ <b>O‘chirish uchun kanal ID</b> yuboring:\n\n" + "\n".join(
                [f"ID: <code>{rid}</code> | {title or ''} {('@'+username) if username else ''} | chat_id={chat_id}"
                 for rid, chat_id, username, title in channels]
            ) + "\n\n❌ Bekor qilish: /cancel"
            admin_wait[uid] = {"mode": "del_channel", "step": 1}
            await c.message.answer(text, parse_mode="HTML")
            return await c.answer()

        if action == "clear_channels":
            await db.clear_channels()
            await c.message.answer("🧹 Kanallar ro‘yxati tozalandi.")
            return await c.answer()

        if action == "add_ad":
            admin_wait[uid] = {"mode": "add_ad", "step": 1}
            await c.message.answer(
                "📢 <b>Reklama qo‘shish</b>\n"
                "Matn yuboring YOKI rasm/video/pdf yuboring.\n"
                "Agar fayl bo‘lsa caption’ga matn yozsangiz ham bo‘ladi.\n"
                "❌ Bekor qilish: /cancel",
                parse_mode="HTML"
            )
            return await c.answer()

        if action == "del_ad":
            ads = await db.list_ads(30)
            if not ads:
                await c.message.answer("Reklamalar yo‘q.")
                return await c.answer()
            text = "🗑 <b>O‘chirish uchun reklama ID</b> yuboring:\n\n" + "\n".join(
                [f"ID: <code>{aid}</code> | {atype}" for aid, atype, _, _ in ads]
            ) + "\n\n❌ Bekor qilish: /cancel"
            admin_wait[uid] = {"mode": "del_ad", "step": 1}
            await c.message.answer(text, parse_mode="HTML")
            return await c.answer()

        if action == "broadcast_ads":
            ads = await db.list_ads(50)
            if not ads:
                await c.message.answer("Reklamalar yo‘q. Avval reklama qo‘shing.")
                return await c.answer()

            users = await db.get_users()
            await c.message.answer(f"🚀 Yuborish boshlandi. Userlar: {len(users)} ta. Reklamalar: {len(ads)} ta.")

            sent = 0
            failed = 0
            for user_id in users:
                for ad_id, ad_type, file_id, text in ads:
                    try:
                        if ad_type == "text":
                            await bot.send_message(user_id, text or "")
                        elif ad_type == "photo":
                            await bot.send_photo(user_id, file_id, caption=(text or ""))
                        elif ad_type == "video":
                            await bot.send_video(user_id, file_id, caption=(text or ""))
                        elif ad_type == "document":
                            await bot.send_document(user_id, file_id, caption=(text or ""))
                        else:
                            await bot.send_message(user_id, text or "")
                        sent += 1
                        await asyncio.sleep(0.05)
                    except Exception:
                        failed += 1
                        await asyncio.sleep(0.05)

            await c.message.answer(f"✅ Tugadi.\nYuborildi: {sent}\nXatolik: {failed}")
            return await c.answer()

        await c.answer()

    # ================= MESSAGES =================
    @dp.message()
    async def all_messages(m: Message):
        uid = m.from_user.id
        await db.add_user(uid)

        # Admin “state” bo‘lsa — faqat admin uchun ishlasin
        if uid in admin_wait and await is_admin(uid, ADMINS):
            st = admin_wait[uid]

            if st["mode"] == "add_movie":
                if st["step"] == 1:
                    st["code"] = (m.text or "").strip()
                    if not st["code"]:
                        return await m.answer("❌ Kod bo‘sh bo‘lmasin. Qayta yuboring. (Bekor: /cancel)")
                    st["step"] = 2
                    return await m.answer("2) Endi kino <b>nomi</b>ni yuboring. (Bekor: /cancel)", parse_mode="HTML")

                if st["step"] == 2:
                    st["title"] = (m.text or "").strip()
                    if not st["title"]:
                        return await m.answer("❌ Nomi bo‘sh bo‘lmasin. (Bekor: /cancel)")
                    st["step"] = 3
                    return await m.answer("3) Endi <b>video</b> (yoki <b>fayl</b>) yuboring. (Bekor: /cancel)", parse_mode="HTML")

                if st["step"] == 3:
                    file_id = None
                    file_type = None

                    if m.video:
                        file_id = m.video.file_id
                        file_type = "video"
                    elif m.document:
                        file_id = m.document.file_id
                        file_type = "document"
                    else:
                        return await m.answer("❌ Video yoki fayl yuboring. (Bekor: /cancel)")

                    try:
                        await db.add_movie(st["code"], st["title"], file_id, file_type)
                        clear_admin_state(uid)
                        return await m.answer("✅ Kino saqlandi. /admin orqali davom eting.")
                    except Exception as e:
                        clear_admin_state(uid)
                        return await m.answer(f"❌ Saqlanmadi. Kod takror bo‘lishi mumkin.\nXato: {e}")

            if st["mode"] == "del_movie":
                try:
                    movie_id = int((m.text or "").strip())
                except:
                    return await m.answer("❌ ID raqam bo‘lishi kerak. (Bekor: /cancel)")
                await db.delete_movie(movie_id)
                clear_admin_state(uid)
                return await m.answer("✅ O‘chirildi (agar mavjud bo‘lsa).")

            if st["mode"] == "add_channel":
                username = (m.text or "").strip()
                if not username.startswith("@"):
                    return await m.answer("❌ @ bilan boshlansin. Masalan: @mychannel (Bekor: /cancel)")
                try:
                    chat = await bot.get_chat(username)
                    await db.add_channel(chat.id, username.lstrip("@"), chat.title)
                    clear_admin_state(uid)
                    return await m.answer(f"✅ Kanal qo‘shildi: {chat.title}")
                except Exception as e:
                    return await m.answer(
                        "❌ Kanal qo‘shilmadi.\n"
                        "Botni kanalga admin qildingizmi?\n"
                        f"Xato: {e}\n(Bekor: /cancel)"
                    )

            if st["mode"] == "del_channel":
                try:
                    rid = int((m.text or "").strip())
                except:
                    return await m.answer("❌ ID raqam bo‘lsin. (Bekor: /cancel)")
                await db.delete_channel(rid)
                clear_admin_state(uid)
                return await m.answer("✅ Kanal o‘chirildi (agar mavjud bo‘lsa).")

            if st["mode"] == "add_ad":
                ad_type = None
                file_id = None
                text = None

                if m.text and not (m.photo or m.video or m.document):
                    ad_type = "text"
                    text = m.text
                elif m.photo:
                    ad_type = "photo"
                    file_id = m.photo[-1].file_id
                    text = m.caption or ""
                elif m.video:
                    ad_type = "video"
                    file_id = m.video.file_id
                    text = m.caption or ""
                elif m.document:
                    ad_type = "document"
                    file_id = m.document.file_id
                    text = m.caption or ""
                else:
                    return await m.answer("❌ Reklama uchun matn/rasm/video/pdf yuboring. (Bekor: /cancel)")

                await db.add_ad(ad_type, file_id, text)
                clear_admin_state(uid)
                return await m.answer("✅ Reklama saqlandi.")

            if st["mode"] == "del_ad":
                try:
                    aid = int((m.text or "").strip())
                except:
                    return await m.answer("❌ ID raqam bo‘lsin. (Bekor: /cancel)")
                await db.delete_ad(aid)
                clear_admin_state(uid)
                return await m.answer("✅ Reklama o‘chirildi (agar mavjud bo‘lsa).")

        # ============== USER FLOW (kino kod) ==============
        ok, kb = await require_subscribe(bot, uid)
        if not ok:
            return await m.answer("❗ Avval kanal(lar)ga a’zo bo‘ling:", reply_markup=kb)

        code = (m.text or "").strip()
        if not code or code.startswith("/"):
            return

        movie = await db.get_movie(code)
        if not movie:
            return await m.answer("❌ Bu kod bo‘yicha kino topilmadi. Kodni tekshirib qayta yuboring.")

        await send_movie(bot, uid, movie)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
