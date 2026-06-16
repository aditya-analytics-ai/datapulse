# 📊 DataPulse

> A professional web-scraping, market intelligence & automated job-tracking platform built with **FastAPI** + **React (Vite)** + **WhatsApp AI Tracker**.

---

## 🚀 Features

### 🌐 Web Scraping Platform
- 🔍 **Universal Web Scraper** — Scrape structured data from any URL
- 🛒 **E-commerce Extractors** — Specialized support for Amazon & Flipkart product listings
- 💼 **LinkedIn Job Scraper** — Extract job postings from LinkedIn
- 📄 **Multi-format Support** — Tables, articles, JSON-LD, PDFs
- 📈 **Job Market Intelligence** — Visualize trends via Remotive API
- 🗂️ **Scrape History** — Browse, revisit, and export all past results
- 📤 **Data Export** — Download as CSV, Excel, or JSON
- 🔐 **Authentication** — JWT-based login + Google OAuth
- ⚡ **Real-time UI** — Animated React frontend with Framer Motion & Recharts

### 📱 WhatsApp AI Job Tracker *(New!)*
- 🤖 **AI-powered Extraction** — Gemini AI (+ Groq fallback) parses job details from raw WhatsApp messages
- 🔔 **Telegram Alerts** — Instant notifications for high-relevance job matches (score ≥ 65/100)
- 📊 **Google Sheets Logging** — All jobs auto-logged to a spreadsheet
- 🔁 **Fully Automated** — Runs every 10 minutes, hands-free
- 🧠 **Smart Deduplication** — SQLite-based; never processes the same message twice
- 🎯 **Relevance Scoring** — Matches jobs against your personal profile (roles, skills, salary, location)

---

## 🛠️ Tech Stack

| Layer              | Technology                                          |
|--------------------|-----------------------------------------------------|
| Backend            | Python · FastAPI · MySQL · Playwright               |
| Frontend           | React · Vite · Framer Motion · Recharts             |
| Auth               | JWT · Google OAuth 2.0                              |
| WhatsApp Tracker   | Playwright · Gemini AI · Groq · APScheduler         |
| Notifications      | Telegram Bot API · Google Sheets API                |
| Storage            | MySQL (main) · SQLite (dedup)                       |

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL

### 1. Clone the repo

```bash
git clone https://github.com/aditya-analytics-ai/datapulse.git
cd datapulse
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` → `.env` and fill in your values:

```bash
cp .env.example .env
```

Import the database schema:

```bash
mysql -u root -p < backend/setup_db.sql
```

Start the backend:

```bash
python -m uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at **http://localhost:5173**

---

## 📱 WhatsApp AI Job Tracker Setup

> Monitors WhatsApp job groups → extracts jobs with AI → alerts you on Telegram.

See the full guide: **[whatsapp_tracker/SETUP.md](whatsapp_tracker/SETUP.md)**

### Quick Start

```bash
# 1. Install dependencies
pip install -r whatsapp_tracker/requirements.txt

# 2. Fill in your keys in .env (GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

# 3. Edit your job profile
#    Open whatsapp_tracker/config.py → set your roles, skills, salary

# 4. One-time WhatsApp login (scan QR code)
python whatsapp_tracker/first_run.py

# 5. Find your group names
python whatsapp_tracker/list_groups.py

# 6. Start the tracker (runs every 10 minutes)
python whatsapp_tracker/scheduler.py
```

### What Happens Each Cycle

```
Every 10 minutes:
  1. Opens WhatsApp Web with saved session (no QR needed again)
  2. Reads last 50 messages from each target group
  3. Drops already-seen messages (SQLite dedup)
  4. Keyword filter → skips non-job messages (saves AI quota)
  5. Gemini AI → extracts title, company, skills, salary, contact
  6. Scores job relevance against your profile (0–100)
  7. Saves ALL jobs → Google Sheets
  8. Telegram alert → only if score ≥ 65
```

### Sample Telegram Alert

```
🔥 New Job Match!  (Score: 88/100)

💼 Python Backend Developer
🏢 FinTech Startup
📍 Remote
💰 8-12 LPA
🛠️ Python, FastAPI, PostgreSQL, Docker
👔 Full-time
🎓 2-4 years
📣 From: Python Jobs India
```

---

## 🔑 Environment Variables

See [`.env.example`](.env.example) for all required variables.

> ⚠️ **Never commit your real `.env` file.** It is already in `.gitignore`.

---

## 📁 Project Structure

```
datapulse/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── routes/              # API route handlers
│   │   ├── scrapers/            # 8 specialized data extractors
│   │   ├── analyzers/           # Job market intelligence
│   │   ├── models/              # SQLAlchemy models
│   │   └── exporters/           # CSV / Excel / JSON export
│   ├── requirements.txt
│   └── setup_db.sql
├── frontend/
│   ├── src/
│   │   ├── components/          # Sidebar, Layout
│   │   ├── pages/               # Scraper, History, JobMarket, etc.
│   │   └── api/
│   ├── package.json
│   └── vite.config.js
├── whatsapp_tracker/            # ← Automated job tracker
│   ├── config.py                # ✏️  Edit this — your profile & keys
│   ├── first_run.py             # Run once for WhatsApp QR scan
│   ├── list_groups.py           # List your WhatsApp groups
│   ├── scheduler.py             # Main runner (keep this running)
│   ├── wa_scraper.py            # Playwright WhatsApp Web bot
│   ├── ai_extractor.py          # Gemini + Groq AI extraction
│   ├── keyword_filter.py        # Fast pre-filter
│   ├── telegram_notifier.py     # Telegram alerts
│   ├── sheets_writer.py         # Google Sheets logging
│   ├── dedup_store.py           # SQLite deduplication
│   └── SETUP.md                 # Full setup guide
├── .env.example                 # ← copy this to .env
└── README.md
```

---

## 📄 License

MIT
