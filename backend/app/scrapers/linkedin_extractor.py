"""
LinkedIn Jobs extractor — parses public job search result pages
into structured rows: title, company, location, salary, posted_date, url.

LinkedIn uses obfuscated CSS classes that change frequently, so this uses
multiple selector strategies and semantic patterns as fallbacks.
"""
from bs4 import BeautifulSoup
import re


def is_linkedin_url(url: str) -> bool:
    return "linkedin." in url.lower() or "linkedin.com" in url.lower()


def extract_linkedin_jobs(html: str, base_url: str = "") -> dict:
    """
    Parse LinkedIn job search page HTML into structured job rows.
    """
    soup = BeautifulSoup(html, "lxml")
    jobs = []

    cards = _find_job_cards(soup)

    for card in cards:
        try:
            job = _parse_job_card(card, base_url)
            if job.get("title") and len(job["title"]) > 3:
                jobs.append(job)
        except Exception:
            continue

    jobs = _dedupe(jobs)

    return {
        "page_type": "linkedin_jobs",
        "source": base_url,
        "total": len(jobs),
        "columns": ["title", "company", "location", "salary", "employment_type", "posted_date", "url"],
        "jobs": jobs,
    }


def _find_job_cards(soup: BeautifulSoup) -> list:
    """Find job card elements using multiple strategies."""
    candidates = []

    # Strategy 1: cards with data-entity-urn (most reliable)
    candidates = soup.select('[data-entity-urn*="jobPosting"], [data-entity-urn*="job"]')

    # Strategy 2: common LinkedIn job card classes (may be obfuscated)
    if len(candidates) < 3:
        candidates = soup.select(
            '[class*="job-card"], [class*="jobCard"], '
            '[class*="job-search"], [class*="jobSearch"], '
            '[class*="base-search-card"], li[class*="jobs-"]'
        )

    # Strategy 3: any list item or div containing job-like patterns
    if len(candidates) < 3:
        for el in soup.find_all(["li", "div"], recursive=True):
            if el.get("data-entity-urn") or el.get("data-occludable-job-id"):
                candidates.append(el)
            elif el.find("a", href=re.compile(r"/jobs/view|/jobs/search|/jobs/collections")):
                text = el.get_text(strip=True)[:500]
                # Must look like a job listing: has a recognizable job title + company-like text
                if re.search(r"(applied|saved|promoted|remote|onsite|hybrid)", text, re.IGNORECASE):
                    candidates.append(el)
                elif el.find("img", alt=True):
                    candidates.append(el)

    # Strategy 4: scrape all links pointing to job listings
    if len(candidates) < 3:
        seen = set()
        for a in soup.find_all("a", href=re.compile(r"/jobs/view/\d+")):
            parent = a.parent
            while parent and parent.name not in ("li", "div", "section"):
                parent = parent.parent
            if parent and id(parent) not in seen:
                seen.add(id(parent))
                candidates.append(parent)

    # Strategy 5: look for elements with company-like + job-title-like text pairs
    if len(candidates) < 3:
        candidates = _find_job_slots(soup)

    return candidates[:100]


def _find_job_slots(soup: BeautifulSoup) -> list:
    """Heuristic: find elements that contain job-like text patterns."""
    candidates = []
    for el in soup.find_all(["div", "li"]):
        text = el.get_text(strip=True)[:500]
        # A job card should have: a job-like title, a company-like name, and location indicator
        has_title = bool(re.search(r"(engineer|developer|manager|analyst|designer|associate|intern|lead|director|specialist|consultant)", text, re.IGNORECASE))
        has_company = bool(re.search(r"(at\s+[A-Z][a-z]+|company|inc\.|corp|ltd|llc)", text, re.IGNORECASE))
        has_location = bool(re.search(r"(remote|hybrid|onsite|united\s*states|india|[\w\s]+,\s*[A-Z]{2})", text, re.IGNORECASE))

        score = sum([has_title, has_company, has_location])
        # Also check for salary indicator
        if re.search(r"[\u20b9\$£€]\s*[\d,.kKmbBM]+", text):
            score += 1

        if score >= 2:
            candidates.append(el)

    return candidates[:80]


def _parse_job_card(card, base_url: str) -> dict:
    title = _extract_title(card)
    company = _extract_company(card)
    location = _extract_location(card)
    salary = _extract_salary(card)
    posted_date = _extract_posted_date(card)
    employment_type = _extract_employment_type(card)
    url = _extract_url(card, base_url)

    return {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "posted_date": posted_date,
        "employment_type": employment_type,
        "url": url,
    }


def _extract_title(card) -> str:
    # Priority 1: anchor with job view link
    for a in card.select("a[href*='/jobs/view/'], a[href*='/jobs/search']"):
        txt = a.get_text(strip=True)
        # Filter out generic text like company names
        if txt and len(txt) > 3 and not re.match(r"^(view|apply|save|share|job)$", txt, re.IGNORECASE):
            return txt[:200]

    # Priority 2: strong/b tags (often used for job title)
    for el in card.select("strong, b"):
        txt = el.get_text(strip=True)
        if len(txt) > 5:
            return txt[:200]

    # Priority 3: aria-label that looks like a job title
    for el in card.find_all(attrs={"aria-label": True}):
        lbl = el["aria-label"]
        if len(lbl) > 5 and re.search(r"(engineer|developer|manager)", lbl, re.IGNORECASE):
            return lbl[:200]

    # Priority 4: first large link text
    for a in card.find_all("a"):
        txt = a.get_text(strip=True)
        if len(txt) > 10:
            return txt[:200]

    # Priority 5: image alt text
    for img in card.find_all("img", alt=True):
        alt = img.get("alt", "").strip()
        if len(alt) > 10:
            return alt[:200]

    return ""


def _extract_company(card) -> str:
    # Priority 1: specific LinkedIn selectors
    for sel in [
        '[class*="company-name"], [class*="companyName"], '
        '[class*="subtitle"], [class*="sub-title"], '
        '[class*="org-name"], [class*="orgName"]'
    ]:
        el = card.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if txt and len(txt) > 1:
                return txt[:100]

    # Priority 2: span or div next to "at" pattern
    text = card.get_text()
    m = re.search(r"(?:at|via)\s+([A-Z][A-Za-z0-9\s&.]+?)(?:\s*[•··]|\s+[\d.,]|\s+[A-Z]{2}|\s*$)", text)
    if m:
        return m.group(2).strip()[:100]

    # Priority 3: any heading-sized text that isn't the title
    candidates = []
    for el in card.find_all(["h3", "h4", "span"]):
        txt = el.get_text(strip=True)
        if txt and len(txt) > 1 and len(txt) < 60:
            candidates.append(txt)
    if candidates:
        return candidates[0][:100]

    return ""


def _extract_location(card) -> str:
    # Priority 1: known LinkedIn location selectors
    for sel in [
        '[class*="location"], [class*="metadata-item"], '
        '[class*="bullet"], [class*="insight"]'
    ]:
        el = card.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if txt and not re.search(r"(hour|year|month|salary|k\b)", txt, re.IGNORECASE):
                return txt[:100]

    # Priority 2: text matching location patterns
    text = card.get_text()
    m = re.search(r"(remote|hybrid|onsite|on-site|telécommuting)\s*[•··]?\s*([\w\s,]+)", text, re.IGNORECASE)
    if m:
        return m.group(0).strip()[:100]

    # Priority 3: any short text containing a comma (city, state pattern)
    for el in card.find_all(["span", "div"]):
        txt = el.get_text(strip=True)
        if re.search(r"^[\w\s]+,\s*[A-Z]{2}", txt) or re.search(r"^(remote|hybrid|onsite)", txt, re.IGNORECASE):
            return txt[:100]

    return ""


def _extract_salary(card) -> str:
    text = card.get_text()
    m = re.search(r"[\u20b9\$£€]\s*[\d,.kKmbBM]+\s*[-–to]+\s*[\u20b9\$£€]\s*[\d,.kKmbBM]+", text)
    if m:
        return m.group()
    m = re.search(r"(?:salary|pay|compensation)[:\s]*([\u20b9\$£€][\d,.kKmbBM]+)", text, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def _extract_posted_date(card) -> str:
    # Priority 1: time tags
    for time_tag in card.find_all("time"):
        dt = time_tag.get("datetime", "")
        if dt:
            return dt[:20]
        txt = time_tag.get_text(strip=True)
        if txt:
            return txt[:50]

    # Priority 2: text patterns like "3 days ago", "1 week ago", "just now"
    text = card.get_text()
    m = re.search(r"(\d+\s+(hour|day|week|month|minute|min|hr)\s*ago|just\s*now|today|yesterday)", text, re.IGNORECASE)
    if m:
        return m.group(0)

    # Priority 3: specific LinkedIn date selectors
    for sel in ['[class*="listdate"], [class*="list-date"], [class*="posted"], [class*="time"]']:
        el = card.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if txt:
                return txt[:50]

    return ""


def _extract_employment_type(card) -> str:
    """Extract Remote / Hybrid / On-site / Contract / Full-time badge."""
    text = card.get_text()

    # Priority 1: look for known employment type patterns
    patterns = [
        (r"\bremote\b", "Remote"),
        (r"\bhybrid\b", "Hybrid"),
        (r"\bonsite\b|\bon-site\b", "On-site"),
        (r"\bin[- ]office\b", "On-site"),
        (r"\bfull[- ]time\b|\bft\b", "Full-time"),
        (r"\bpart[- ]time\b|\bpt\b", "Part-time"),
        (r"\bcontract\b", "Contract"),
        (r"\btemporary\b|\btemp\b", "Temporary"),
        (r"\binternship\b", "Internship"),
        (r"\bfreelance\b", "Freelance"),
    ]

    found = []
    for pattern, label in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Avoid matching salary or location text
            if label in ("Remote", "Hybrid", "On-site"):
                # Make sure it's a standalone badge, not part of location
                pass
            found.append(label)

    if found:
        return " / ".join(sorted(set(found), key=lambda x: ["Remote", "Hybrid", "On-site", "Full-time", "Part-time", "Contract", "Temporary", "Internship", "Freelance"].index(x)))

    # Priority 2: specific LinkedIn badge elements
    for sel in [
        '[class*="workplace"], [class*="workplace-type"], '
        '[class*="employment"], [class*="job-type"], '
        '[class*="insight"], [class*="metadata-item"]'
    ]:
        el = card.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            normalized = txt.lower()
            if "remote" in normalized:
                return "Remote"
            if "hybrid" in normalized:
                return "Hybrid"
            if "on-site" in normalized or "onsite" in normalized:
                return "On-site"
            if "full-time" in normalized:
                return "Full-time"
            if "contract" in normalized:
                return "Contract"
            if txt:
                return txt[:50]

    return ""


def _extract_url(card, base_url: str) -> str:
    for a in card.find_all("a", href=True):
        href = a["href"]
        if "/jobs/view/" in href:
            if href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                domain = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else "https://www.linkedin.com"
                return domain + href.split("?")[0]
            return href.split("?")[0]
    # Fallback: first link
    a = card.find("a", href=True)
    if a:
        href = a["href"]
        if href.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            domain = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else "https://www.linkedin.com"
            return domain + href
        return href
    return ""


def _dedupe(jobs: list) -> list:
    seen = set()
    unique = []
    for j in jobs:
        key = f"{j.get('title', '')}|{j.get('company', '')}|{j.get('url', '')}"
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique
