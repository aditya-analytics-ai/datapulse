# WhatsApp AI Job Tracker — Setup Guide

## What you need (all free)

| Tool | Purpose | Time to setup |
|------|---------|---------------|
| Gemini API key | AI job extraction | 2 min |
| Telegram Bot | Job notifications | 3 min |
| Google Sheets service account | Job logging | 5 min |

---

## Step 1 — Get Gemini API Key (Free)

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with Google → click **Get API Key**
3. Copy the key → paste in `config.py` → `GEMINI_API_KEY`

---

## Step 2 — Create Telegram Bot (Free)

1. Open Telegram → search **@BotFather** → send `/newbot`
2. Follow prompts → choose a name → copy the **token**
3. Paste token in `config.py` → `TELEGRAM_BOT_TOKEN`
4. Send `/start` to your new bot in Telegram
5. Open this URL in browser (replace TOKEN):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
6. Find `"id"` inside `"chat"` in the response → that's your **chat_id**
7. Paste in `config.py` → `TELEGRAM_CHAT_ID`

---

## Step 3 — Google Sheets (Free, Optional but Recommended)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Search **"Google Sheets API"** → Enable it
4. Search **"Google Drive API"** → Enable it
5. Go to **IAM & Admin → Service Accounts** → Create Service Account
6. Name it anything → Create → Done
7. Click the service account → **Keys** tab → **Add Key** → JSON
8. Download the JSON file → save as `whatsapp_tracker/google_creds.json`
9. ✅ The sheet will be auto-created when the tracker runs

---

## Step 4 — First WhatsApp Session (One Time Only)

```bash
# From the datapulse root folder:
python whatsapp_tracker/first_run.py
```

- A Chrome window opens
- Scan QR with WhatsApp: **Settings → Linked Devices → Link a Device**
- Window closes automatically after login
- Session saved to `whatsapp_tracker/wa_session/`

---

## Step 5 — Find Your Group Names

```bash
python whatsapp_tracker/list_groups.py
```

- Lists all your WhatsApp chats
- Copy exact group names → paste into `config.py` → `TARGET_GROUPS`

---

## Step 6 — Edit Your Profile in config.py

```python
PROFILE = {
    "roles": ["Python Developer", "Data Engineer"],   # ← YOUR target roles
    "skills": ["Python", "SQL", "FastAPI"],            # ← YOUR skills
    "location": "Remote",                              # ← preferred location
    "experience": "1-3 years",                        # ← your experience
    "salary_min_lpa": 5,                              # ← minimum salary
}

TARGET_GROUPS = [
    "Python Jobs India",     # ← exact names from list_groups.py
    "Hiring Hub 2024",
]
```

---

## Step 7 — Run the Tracker

```bash
# Start the full pipeline (runs every 10 minutes)
python whatsapp_tracker/scheduler.py
```

Keep this running in a terminal. Minimize and forget it!

---

## What Happens Each Cycle

```
Every 10 minutes:
  1. Opens WhatsApp Web (headless) with saved session
  2. Reads last 50 messages from each group
  3. Drops already-seen messages (SQLite dedup)
  4. Keyword filter → drops non-job messages (saves Gemini quota)
  5. Gemini AI → extracts title, company, skills, salary, contact...
  6. Scores job relevance against YOUR profile (0-100)
  7. Saves ALL jobs → Google Sheets
  8. Telegram alert → only if score ≥ 65 (configurable)
```

---

## Sample Telegram Notification

```
🔥 New Job Match!  (Score: 88/100)

💼 Python Backend Developer
🏢 FinTech Startup
📍 Remote
💰 8-12 LPA
🛠️ Python, FastAPI, PostgreSQL, Docker
👔 Full-time
🎓 2-4 years
📞 +91 98765XXXXX
📣 From: Python Jobs India

💡 Strong Python + Remote match. Salary above minimum.
```

---

## File Structure

```
whatsapp_tracker/
├── config.py           ← ✏️  EDIT THIS — your profile & keys
├── first_run.py        ← Run once for QR scan
├── list_groups.py      ← Run to see group names
├── scheduler.py        ← Main runner (keep this running)
├── wa_scraper.py       ← Playwright WhatsApp Web bot
├── keyword_filter.py   ← Fast pre-filter
├── ai_extractor.py     ← Gemini AI extraction
├── sheets_writer.py    ← Google Sheets logging
├── telegram_notifier.py← Telegram alerts
├── dedup_store.py      ← SQLite deduplication
├── wa_session/         ← Saved WhatsApp session (auto-created)
├── dedup.db            ← Seen messages DB (auto-created)
└── google_creds.json   ← ← Download from Google Cloud Console
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Session not found" | Run `first_run.py` again |
| "WhatsApp Web did not load" | Re-run `first_run.py` to refresh session |
| Group not found | Run `list_groups.py` and check exact spelling |
| Gemini errors | Check API key, ensure free quota not exhausted |
| Telegram not sending | Check bot token and chat_id |
