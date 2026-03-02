import os

# Telegram credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Bot info
BOT_USERNAME = os.getenv("MentionAIbot")
UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "https://t.me/Ace_networkop")

# Owner (IMPORTANT)
OWNER_ID = int(os.getenv("OWNER_ID"))  # <-- ADD THIS

# Database
MONGO_URI = os.getenv("MONGO_URI")
