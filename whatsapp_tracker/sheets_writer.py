"""
sheets_writer.py — Append extracted job data to Google Sheets.

Setup (one-time, free):
1. Go to console.cloud.google.com → New Project
2. Enable "Google Sheets API" and "Google Drive API"
3. Create a Service Account → download JSON key
4. Save key as  whatsapp_tracker/google_creds.json
5. Open your Google Sheet → Share → add the service account email as Editor
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Timestamp", "Group", "Title", "Company", "Skills",
    "Salary", "Location", "Job Type", "Experience",
    "Contact", "Apply Link", "Score", "Reason", "Raw Message",
]

_sheet_cache = {}


def _get_sheet(creds_file: str, sheet_name: str):
    if sheet_name in _sheet_cache:
        return _sheet_cache[sheet_name]

    creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        sh = client.open(sheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        sh = client.create(sheet_name).sheet1
        sh.append_row(HEADERS)
        print(f"  📊 Created new Google Sheet: '{sheet_name}'")
        # Make it viewable by anyone with the link
        sh.spreadsheet.share(None, perm_type="anyone", role="reader")

    _sheet_cache[sheet_name] = sh
    return sh


def write_job(job: dict, group: str, raw_text: str, creds_file: str, sheet_name: str):
    """Append a single extracted job row to the sheet."""
    sheet = _get_sheet(creds_file, sheet_name)
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        group,
        job.get("title") or "",
        job.get("company") or "",
        ", ".join(job.get("skills") or []),
        job.get("salary") or "",
        job.get("location") or "",
        job.get("job_type") or "",
        job.get("experience_required") or "",
        job.get("contact") or "",
        job.get("apply_link") or "",
        job.get("relevance_score", 0),
        job.get("relevance_reason") or "",
        raw_text[:400],
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")
