from pyrogram import filters
from database import add_user, add_group

def register(app):

    @app.on_message(filters.private)
    async def save_user(_, m):
        await add_user(m.from_user.id)

    @app.on_message(filters.group)
    async def save_group(_, m):
        await add_group(m.chat.id)
