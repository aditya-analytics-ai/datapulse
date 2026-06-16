"""
scheduler.py - Main pipeline runner with APScheduler.
Run: python whatsapp_tracker/scheduler.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

from whatsapp_tracker.config import (
    PROFILE, TARGET_GROUPS, GEMINI_API_KEY, GROQ_API_KEY,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEET_NAME,
    NOTIFY_THRESHOLD, MESSAGES_PER_GROUP,
    POLL_INTERVAL_MINUTES, HEADLESS,
)
from whatsapp_tracker import wa_scraper, keyword_filter, ai_extractor
from whatsapp_tracker import dedup_store, sheets_writer, telegram_notifier

USE_SHEETS = os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE)


def safe_print(msg):
    """Print with unicode handling for Windows console."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode(), flush=True)


def log(msg):
    """Print with immediate flush so output appears in real time."""
    safe_print(msg)


def run_pipeline():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log(f"\n{'='*55}")
    log(f"  [RUN] Pipeline started - {now}")
    log(f"{'='*55}")

    # 1 - Scrape
    try:
        log(f"  [1/4] Scraping {len(TARGET_GROUPS)} groups...")
        raw_messages = wa_scraper.scrape_groups(
            TARGET_GROUPS, max_msgs=MESSAGES_PER_GROUP, headless=HEADLESS
        )
    except Exception as e:
        log(f"  [ERROR] Scraper failed: {e}")
        telegram_notifier.send_system_alert(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, f"Scraper error: {e}")
        return

    log(f"  [2/4] {len(raw_messages)} messages scraped")

    # 2 - Dedup
    new_messages = [m for m in raw_messages if not dedup_store.is_seen(m["hash"])]
    log(f"        {len(new_messages)} are new (unseen)")

    if not new_messages:
        log("  [OK] Nothing new this cycle.")
        return

    # 3 - Keyword filter
    job_candidates = keyword_filter.filter_messages(new_messages)
    log(f"  [3/4] {len(job_candidates)} pass keyword filter")

    # 4 - AI + output
    log(f"  [4/4] Running AI extraction...")
    jobs_found = 0
    for msg in job_candidates:
        dedup_store.mark_seen(msg["hash"], msg["group"])
        preview = msg['text'][:55].replace('\n', ' ')
        safe_print(f"\n        Group : {msg['group']}")
        safe_print(f"        Msg   : {preview}...")

        job = ai_extractor.extract_job(msg["text"], PROFILE, GEMINI_API_KEY, GROQ_API_KEY)

        if not job or not job.get("is_job"):
            log(f"        -> Not a job, skipped")
            continue

        score = job.get("relevance_score", 0)
        title = job.get("title", "Unknown")
        safe_print(f"        -> JOB: {title} | Score: {score}/100")
        jobs_found += 1

        if USE_SHEETS:
            try:
                sheets_writer.write_job(job, msg["group"], msg["text"],
                                         GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEET_NAME)
                log(f"        -> Saved to Sheets")
            except Exception as e:
                log(f"        -> Sheets error: {e}")

        if score >= NOTIFY_THRESHOLD:
            telegram_notifier.send_job_alert(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, job, msg["group"])
            log(f"        -> Telegram sent!")

    # Mark rest as seen
    for msg in new_messages:
        if not dedup_store.is_seen(msg["hash"]):
            dedup_store.mark_seen(msg["hash"], msg["group"])

    log(f"\n  [DONE] {jobs_found} jobs found this run")
    log(f"         Next run in {POLL_INTERVAL_MINUTES} minutes.\n")


if __name__ == "__main__":
    dedup_store.init_db()
    dedup_store.prune_old(days=30)

    log("DataPulse - WhatsApp AI Job Tracker")
    log(f"  Groups    : {len(TARGET_GROUPS)}")
    log(f"  Interval  : {POLL_INTERVAL_MINUTES} min")
    log(f"  Threshold : score >= {NOTIFY_THRESHOLD}")
    log(f"  Sheets    : {'yes' if USE_SHEETS else 'no'}")
    log("  Ctrl+C to stop\n")

    run_pipeline()

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(run_pipeline, "interval", minutes=POLL_INTERVAL_MINUTES, id="wa_tracker")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log("\n[*] Tracker stopped.")
