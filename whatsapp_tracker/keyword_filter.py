"""
keyword_filter.py — Fast pre-filter before calling Gemini.
Saves API quota by dropping obvious non-job messages.
"""

JOB_KEYWORDS = [
    # English
    "hiring", "job", "vacancy", "opening", "position", "role", "opportunity",
    "apply", "jd", "job description", "fresher", "experience", "recruiter",
    "lpa", "ctc", "salary", "package", "urgent", "immediate", "requirement",
    "full time", "full-time", "part time", "internship", "remote", "wfh",
    "work from home", "joining", "interview", "shortlist",
    # Hinglish / common Indian job group phrases
    "naukri", "job hai", "joining chahiye", "requirement hai", "cv share",
    "resume send", "candidate", "profile share", "refer", "referral",
]

SPAM_SIGNALS = [
    "forward this", "share this message", "chain message",
    "lottery", "prize", "winner", "congratulations you have been selected",
    "earn money from home", "mlm", "network marketing",
]

MIN_LENGTH = 20   # messages shorter than this are probably not job posts


def is_job_message(text: str) -> bool:
    """Return True if message likely contains a job posting."""
    lower = text.lower()

    # Too short
    if len(text.strip()) < MIN_LENGTH:
        return False

    # Obvious spam
    if any(spam in lower for spam in SPAM_SIGNALS):
        return False

    # Must have at least one job keyword
    return any(kw in lower for kw in JOB_KEYWORDS)


def filter_messages(messages: list[dict]) -> list[dict]:
    """Filter a list of message dicts, keeping only likely job postings."""
    return [m for m in messages if is_job_message(m["text"])]
