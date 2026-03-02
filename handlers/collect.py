from pyrogram import filters
from database import add_user, add_group


def collect_handler(app):

    @app.on_message(filters.private)
    async def collect_user(client, message):
        if message.from_user:
            add_user(message.from_user.id)

    @app.on_message(filters.group | filters.supergroup)
    async def collect_group(client, message):
        add_group(message.chat.id)
