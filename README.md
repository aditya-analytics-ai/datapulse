# 📊 DataPulse

> A professional web-scraping & market intelligence platform built with **FastAPI** + **React (Vite)**.

---

## 🚀 Features

- 🔍 **Web Scraper** — Scrape structured data from any URL, including Amazon product listings
- 📈 **Market Intelligence Dashboard** — Visualize trends and pricing data
- 🗂️ **Scrape History** — Browse and revisit all past scrape results
- 🔐 **Authentication** — JWT-based login + Google OAuth
- ⚡ **Real-time UI** — Animated React frontend with Framer Motion & Recharts

---

## 🛠️ Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Python · FastAPI · MySQL · Playwright |
| Frontend  | React · Vite · Framer Motion · Recharts |
| Auth      | JWT · Google OAuth 2.0              |

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/datapulse.git
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
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at **http://localhost:5173**

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
│   │   ├── main.py          # FastAPI entry point
│   │   ├── routers/         # API route handlers
│   │   └── ...
│   ├── requirements.txt
│   └── setup_db.sql
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
├── .env.example             # ← copy this to .env
└── README.md
```

---

## 📄 License

MIT
