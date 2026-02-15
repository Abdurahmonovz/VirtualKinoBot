from aiogram import Bot
from aiogram.types import ChatMemberLeft, ChatMemberBanned

async def is_admin(user_id: int, admins: set[int]) -> bool:
    return user_id in admins

async def check_user_subscriptions(bot: Bot, user_id: int, channels: list[tuple]) -> bool:
    """
    channels rows: (id, chat_id, username, title)
    bot kanal(lar)da admin bo‘lsa, chat_id bo‘yicha tekshiradi.
    Agar chat_id bo‘lmasa (faqat username bo‘lsa) ham urinadi.
    """
    for _, chat_id, username, _ in channels:
        target = None
        if chat_id and chat_id != 0:
            target = chat_id
        elif username:
            target = username

        if not target:
            continue

        try:
            member = await bot.get_chat_member(chat_id=target, user_id=user_id)
            if isinstance(member, (ChatMemberLeft, ChatMemberBanned)) or member.status in ("left", "kicked"):
                return False
        except Exception:
            # bot kanalni ko‘rmasa yoki huquqi bo‘lmasa — majburiy a’zolikni o‘tolmaydi.
            return False

    return True
