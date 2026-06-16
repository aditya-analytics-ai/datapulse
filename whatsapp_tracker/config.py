"""
config.py — DataPulse WhatsApp AI Job Tracker configuration.
All API keys are loaded from the root .env file — never hardcoded here.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load from project root .env
load_dotenv(Path(__file__).parent.parent / ".env")

# ── YOUR JOB PROFILE ─────────────────────────────────
# Edit this to match what YOU are looking for
PROFILE = {
    "roles": [
        "Software Engineer", "Backend Developer", "Full Stack Developer",
        "Frontend Developer", "Python Developer", "Java Developer",
        "DevOps Engineer", "Data Engineer", "ML Engineer",
        "QA Engineer", "System Engineer", "Application Developer"
    ],
    "skills": [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
        "Spring Boot", "SQL", "PostgreSQL", "MySQL", "MongoDB", "AWS",
        "Docker", "Kubernetes", "Git", "Linux", "REST API", "Microservices",
        "FastAPI", "Django", "Flask", "Angular", "Vue"
    ],
    "location": "Any",            # e.g. "Remote", "Bangalore", "Any"
    "experience": "0-3 years",    # e.g. "Fresher", "1-3 years"
    "salary_min_lpa": 3,
}

# ── WHATSAPP GROUPS TO MONITOR ───────────────────────
# Run: python whatsapp_tracker/list_groups.py  to see your exact group names
TARGET_GROUPS = [
    "Indian Hire Hub | 03",
    "Daily IT Jobs Update (Group 02)",
]

# ── API KEYS (loaded from .env) ──────────────────────
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")
TELEGRAM_BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID", "")

# ── GOOGLE SHEETS ────────────────────────────────────
GOOGLE_SHEETS_CREDENTIALS_FILE = "whatsapp_tracker/google_creds.json"
GOOGLE_SHEET_NAME = "DataPulse Job Tracker"

# ── BEHAVIOUR ────────────────────────────────────────
NOTIFY_THRESHOLD        = 30    # Telegram alert only if score >= this
MESSAGES_PER_GROUP      = 50    # Recent messages to read per group
POLL_INTERVAL_MINUTES   = 10    # Poll frequency (minimum 5)
HEADLESS                = False  # WhatsApp Web needs visible browser on Windows
