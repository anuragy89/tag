# 🤖 TagMaster Bot v2

> Ultimate Telegram Group Tagging Bot — 8 modes, MongoDB, human-like messages, spam protection & full admin controls!

---

## ✨ What's New in v2

- ✅ **MongoDB** (via `motor` async driver) — persistent storage that survives Heroku restarts
- ✅ **`/broadcast`** — fully working with live progress updates + blocked-user counting
- ✅ **`/stats`** — live counts directly from MongoDB
- ✅ **`@admin` / `@all` text triggers** — works as plain text in groups (not just slash commands)
- ✅ **Proper `new_chat_member` handler** — bot sends welcome msg when added to group
- ✅ **Async tag state** — pause/stop works instantly via MongoDB, no race conditions
- ✅ **Task crash recovery** — if a tagging task crashes, state resets to `idle` automatically
- ✅ **Broadcast blocked-user detection** — distinguishes sent / blocked / failed counts

---

## 📋 Commands

### 🏷️ Tagging (Group Admins Only)
| Command | Description |
|---|---|
| `/hitag` | Tag all — Hindi funny+flirty 🇮🇳 |
| `/entag` | Tag all — English funny+flirty 🇬🇧 |
| `/gmtag` | Tag all — Good Morning (Hinglish) 🌅 |
| `/gntag` | Tag all — Good Night (Hinglish) 🌙 |
| `/tagall` | Tag all — Hinglish mix (memes+jokes+flirt) 🔥 |
| `/jtag` | Tag all — Jokes (Hinglish) 😂 |
| `/admin <msg>` | Tag all admins — anyone can use, msg optional 👮 |
| `@admin <msg>` | Same as /admin |
| `/all <msg>` | Tag all members — admins only, msg optional 📢 |
| `@all <msg>` | Same as /all |

### ⏸️ Tag Controls (Group Admins Only)
| Command | Description |
|---|---|
| `/stop` | Stop all running tagging 🛑 |
| `/pause` | Pause current tagging ⏸️ |
| `/resume` | Resume paused tagging ▶️ |

### 📊 General
| Command | Description |
|---|---|
| `/start` | Welcome message with inline buttons |
| `/help` | All commands explained |
| `/stats` | Live bot usage stats |

### 👑 Owner Only
| Command | Description |
|---|---|
| `/broadcast <msg>` | Broadcast to all users + groups with progress |

---

## 🚀 Deploy to Heroku

### Step 1 — Get MongoDB Atlas URI (Free)
1. Go to [mongodb.com/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster
3. Go to **Connect → Drivers** → copy the connection string
4. Replace `<password>` with your DB password
5. Your URI looks like: `mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/`

### Step 2 — Deploy

#### Option A: One-Click (after pushing to GitHub)
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

#### Option B: CLI
```bash
# Clone / setup
git clone https://github.com/yourrepo/tagmaster-bot
cd tagmaster-bot
heroku login
heroku create your-bot-name

# Set environment variables
heroku config:set BOT_TOKEN="your_bot_token"
heroku config:set OWNER_ID="your_telegram_user_id"
heroku config:set MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/"
heroku config:set DB_NAME="tagmaster"
heroku config:set UPDATES_CHANNEL="https://t.me/yourchannel"
heroku config:set SUPPORT_GROUP="https://t.me/yourgroup"

# Deploy
git add .
git commit -m "Deploy TagMaster v2"
git push heroku main
heroku ps:scale worker=1

# Check logs
heroku logs --tail
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `OWNER_ID` | ✅ | Your Telegram user ID (from [@userinfobot](https://t.me/userinfobot)) |
| `MONGO_URI` | ✅ | MongoDB connection string (Atlas free tier works) |
| `DB_NAME` | ❌ | Database name (default: `tagmaster`) |
| `UPDATES_CHANNEL` | ❌ | Your updates channel link |
| `SUPPORT_GROUP` | ❌ | Your support group link |

---

## 🔧 Local Development

```bash
# Install
pip install -r requirements.txt

# Create .env (then run with python-dotenv or export manually)
export BOT_TOKEN="your_token"
export OWNER_ID="your_id"
export MONGO_URI="mongodb://localhost:27017"

# Run
python bot.py
```

---

## 📁 Project Structure

```
tagmaster-bot/
├── bot.py          # Main bot — all handlers & logic
├── database.py     # MongoDB (motor async) — all DB operations
├── requirements.txt
├── Procfile        # Heroku worker process
├── runtime.txt     # Python 3.12
├── app.json        # Heroku one-click deploy config
└── README.md
```

---

## 💡 How Member Tracking Works

Members are tracked **automatically** as they send messages in the group.
- No need to manually add members
- Members are stored in MongoDB `group_members` collection
- More active = more members tracked = better tagging coverage

---

## 🛡️ Spam Protection

- **FloodWait auto-handled** — up to 6 retry attempts with exponential backoff
- **3–4 second delay** between each tag chunk
- **5–6 users per message** (Telegram best practice)
- **Pause/Stop instantly via MongoDB** — no waiting for current chunk to finish

---

## 👤 Support

Questions? Join the support group: [t.me/yourgroup](https://t.me/yourgroup)


<p align="center"><a href="https://dashboard.heroku.com/new?template=https://github.com/anuragy89/tag.git"> <img src="https://img.shields.io/badge/Deploy%20On%20Heroku-purple?style=for-the-badge&logo=heroku" width="220" height="38.45"/></a></p>

