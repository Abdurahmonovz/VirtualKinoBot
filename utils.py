from aiogram import Bot

async def is_admin(user_id: int, admins: set[int]) -> bool:
    return user_id in admins

async def check_user_subscriptions(bot: Bot, user_id: int, channels: list[tuple]) -> tuple[bool, str | None]:
    """
    Returns: (ok, error_reason)
    channels rows: (id, chat_id, username, title)
    error_reason can be:
      - "bot_not_admin_or_no_access"
      - "not_subscribed"
      - "unknown"
    """
    for _, chat_id, username, _ in channels:
        target = None
        if chat_id and chat_id != 0:
            target = chat_id
        elif username:
            # username DB’da @siz bo‘lishi mumkin
            target = f"@{username.lstrip('@')}"

        if not target:
            continue

        try:
            member = await bot.get_chat_member(chat_id=target, user_id=user_id)
            status = getattr(member, "status", None)
            # member.status: "creator", "administrator", "member", "restricted", "left", "kicked"
            if status in ("left", "kicked"):
                return False, "not_subscribed"
        except Exception:
            # Bot kanalga kira olmasa / admin bo‘lmasa / privacy bo‘lsa
            return False, "bot_not_admin_or_no_access"

    return True, None
