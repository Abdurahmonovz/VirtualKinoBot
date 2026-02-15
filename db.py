import aiosqlite

class DB:
    def __init__(self, path: str):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY
            )
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS channels(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                username TEXT,
                title TEXT
            )
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS movies(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                title TEXT,
                file_id TEXT,
                file_type TEXT
            )
            """)
            await db.execute("""
            CREATE TABLE IF NOT EXISTS ads(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_type TEXT,
                file_id TEXT,
                text TEXT
            )
            """)
            await db.commit()

    async def add_user(self, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
            await db.commit()

    async def get_users(self):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT user_id FROM users")
            rows = await cur.fetchall()
            return [r[0] for r in rows]

    async def add_channel(self, chat_id: int, username: str | None, title: str | None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO channels(chat_id, username, title) VALUES(?,?,?)",
                (chat_id, username, title)
            )
            await db.commit()

    async def list_channels(self):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT id, chat_id, username, title FROM channels ORDER BY id DESC")
            return await cur.fetchall()

    async def delete_channel(self, row_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM channels WHERE id=?", (row_id,))
            await db.commit()

    async def clear_channels(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM channels")
            await db.commit()

    async def add_movie(self, code: str, title: str, file_id: str, file_type: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO movies(code, title, file_id, file_type) VALUES(?,?,?,?)",
                (code.strip(), title.strip(), file_id, file_type)
            )
            await db.commit()

    async def get_movie(self, code: str):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT id, code, title, file_id, file_type FROM movies WHERE code=?",
                (code.strip(),)
            )
            return await cur.fetchone()

    async def list_movies(self, limit: int = 20):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT id, code, title FROM movies ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return await cur.fetchall()

    async def delete_movie(self, movie_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM movies WHERE id=?", (movie_id,))
            await db.commit()

    async def clear_movies(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM movies")
            await db.commit()

    async def add_ad(self, ad_type: str, file_id: str | None, text: str | None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO ads(ad_type, file_id, text) VALUES(?,?,?)",
                (ad_type, file_id, text)
            )
            await db.commit()

    async def list_ads(self, limit: int = 20):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT id, ad_type, file_id, text FROM ads ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return await cur.fetchall()

    async def delete_ad(self, ad_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM ads WHERE id=?", (ad_id,))
            await db.commit()

    async def clear_ads(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM ads")
            await db.commit()
