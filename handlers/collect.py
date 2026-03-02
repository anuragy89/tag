from pyrogram import filters
from database import add_user, add_group


def collect_handler(app):

    # collect users who start bot in DM
    @app.on_message(filters.private)
    async def collect_user(client, message):
        if message.from_user:
            add_user(message.from_user.id)

    # collect groups where bot is added or used
    @app.on_message(filters.group)
    async def collect_group(client, message):
        if message.chat:
            add_group(message.chat.id)
