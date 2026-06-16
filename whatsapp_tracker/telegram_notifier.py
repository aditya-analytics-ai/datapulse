"""
telegram_notifier.py — Send job match alerts via Telegram Bot.

Setup (free, 2 minutes):
1. Open Telegram → search @BotFather → /newbot → follow steps → copy token
2. Start a chat with your new bot → send /start
3. Get your chat_id: https://api.telegram.org/bot<TOKEN>/getUpdates
4. Paste TOKEN and chat_id into config.py
"""
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def safe_print(msg):
    """Print with unicode handling for Windows console."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode(), flush=True)


def _score_emoji(score: int) -> str:
    if score >= 80:
        return "🔥"
    if score >= 65:
        return "✅"
    return "📌"


def send_job_alert(bot_token: str, chat_id: str, job: dict, group: str):
    """Send a formatted job card to Telegram."""
    score = job.get("relevance_score", 0)
    skills = ", ".join((job.get("skills") or [])[:5]) or "—"

    lines = [
        f"{_score_emoji(score)} *New Job Match!*  _(Score: {score}/100)_",
        "",
        f"💼 *{job.get('title') or 'Unknown Role'}*",
        f"🏢 {job.get('company') or '—'}",
        f"📍 {job.get('location') or '—'}",
        f"💰 {job.get('salary') or '—'}",
        f"🛠️ {skills}",
        f"👔 {job.get('job_type') or '—'}",
        f"🎓 {job.get('experience_required') or '—'}",
        f"📞 {job.get('contact') or '—'}",
        f"📣 From: *{group}*",
    ]

    if job.get("apply_link"):
        lines.append(f"\n🔗 [Apply Here]({job['apply_link']})")

    reason = job.get("relevance_reason", "")
    if reason:
        lines.append(f"\n💡 _{reason}_")

    text = "\n".join(lines)

    try:
        resp = requests.post(
            TELEGRAM_API.format(token=bot_token),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            safe_print(f"    [TELEGRAM] Alert sent  (score {score})")
        else:
            safe_print(f"    [TELEGRAM] Error: {resp.status_code} — {resp.text[:100]}")
    except Exception as e:
        safe_print(f"    [TELEGRAM] Request failed: {e}")


def send_system_alert(bot_token: str, chat_id: str, message: str):
    """Send a plain system/error message to Telegram."""
    try:
        requests.post(
            TELEGRAM_API.format(token=bot_token),
            json={"chat_id": chat_id, "text": f"⚙️ DataPulse: {message}"},
            timeout=10,
        )
    except Exception:
        pass
