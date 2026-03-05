# 🤖 TagMaster Bot

> The ultimate Telegram Group Tagging Bot — 8 tag modes, human-like messages, spam protection & full admin controls!

---

## ✨ Features

| Feature | Details |
|---|---|
| 🏷️ **8 Tagging Modes** | Hindi, English, GM, GN, Jokes, TagAll, Admin Tag, All Tag |
| 😄 **Human-Like Msgs** | Funny, flirty, meme-worthy — feels real! |
| 🛡️ **Spam Protection** | FloodWait + RetryAfter handled automatically |
| ⏸️ **Tag Controls** | Pause / Resume / Stop tagging at any time |
| 📢 **Broadcast** | Send messages to all users & groups |
| 📊 **Stats** | See bot usage stats instantly |
| 💾 **SQLite DB** | Lightweight, zero-config database |

---

## 📋 Commands

### 🏷️ Tagging (Admins Only)
| Command | Description |
|---|---|
| `/hitag` | Tag all — Hindi (funny+flirty) |
| `/entag` | Tag all — English (funny+flirty) |
| `/gmtag` | Tag all — Good Morning (Hinglish) |
| `/gntag` | Tag all — Good Night (Hinglish) |
| `/tagall` | Tag all — Hinglish mix (memes+jokes+flirt) |
| `/jtag` | Tag all — Jokes (Hinglish) |
| `/admin <msg>` | Tag all admins (anyone can use, msg optional) |
| `/all <msg>` | Tag all members (admins, msg optional) |

### ⏸️ Controls (Admins Only)
| Command | Description |
|---|---|
| `/stop` | Stop all running tagging |
| `/pause` | Pause current tagging |
| `/resume` | Resume paused tagging |

### 📊 General
| Command | Description |
|---|---|
| `/start` | Welcome message + buttons |
| `/help` | All commands explained |
| `/stats` | Bot usage stats |
| `/broadcast <msg>` | **Owner only** — Broadcast to all |

---

## 🚀 Deploy to Heroku

### Method 1: One-Click Deploy
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

> Click the button above, fill in your `BOT_TOKEN` and `OWNER_ID`, done!

---

### Method 2: Manual Deploy (CLI)

#### Step 1 — Install Heroku CLI
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows — Download installer from:
# https://devcenter.heroku.com/articles/heroku-cli
```

#### Step 2 — Clone & Setup
```bash
git clone https://github.com/yourrepo/tagmaster-bot
cd tagmaster-bot
heroku login
heroku create your-bot-name
```

#### Step 3 — Set Environment Variables
```bash
heroku config:set BOT_TOKEN="your_bot_token_here"
heroku config:set OWNER_ID="your_telegram_user_id"
heroku config:set UPDATES_CHANNEL="https://t.me/yourchannel"
heroku config:set SUPPORT_GROUP="https://t.me/yourgroup"
```

#### Step 4 — Deploy
```bash
git add .
git commit -m "Initial deploy"
git push heroku main
heroku ps:scale worker=1
```

#### Step 5 — View Logs
```bash
heroku logs --tail
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ Yes | From [@BotFather](https://t.me/BotFather) |
| `OWNER_ID` | ✅ Yes | Your Telegram user ID (from [@userinfobot](https://t.me/userinfobot)) |
| `UPDATES_CHANNEL` | ❌ Optional | Your channel link |
| `SUPPORT_GROUP` | ❌ Optional | Your support group link |

---

## 🔧 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "BOT_TOKEN=your_token_here" > .env
echo "OWNER_ID=your_id_here" >> .env

# Run
python bot.py
```

---

## 📁 Project Structure

```
tagmaster-bot/
├── bot.py          # Main bot logic
├── database.py     # SQLite database layer
├── requirements.txt
├── Procfile        # Heroku process config
├── runtime.txt     # Python version
├── app.json        # Heroku one-click config
└── README.md
```

---

## 💡 Notes

- Bot **automatically tracks members** as they chat in the group
- Tag delays are **3-4 seconds** between chunks to avoid Telegram bans
- **6 users per message** for `/admin` and `/all` commands
- **5 users per message** for all other tag modes
- SQLite DB is stored on Heroku's ephemeral filesystem — for production, consider using a hosted Postgres DB

---

## 👤 Owner

Made with ❤️ | [@YourUsername](https://t.me/yourusername)


<p align="center"><a href="https://dashboard.heroku.com/new?template=https://github.com/anuragy89/tag.git"> <img src="https://img.shields.io/badge/Deploy%20On%20Heroku-purple?style=for-the-badge&logo=heroku" width="220" height="38.45"/></a></p>

