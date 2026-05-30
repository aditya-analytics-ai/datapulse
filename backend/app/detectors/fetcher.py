import requests
import logging
import re
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# Block requests to internal/private IPs (SSRF prevention)
_BLOCKED_HOSTS = re.compile(
    r"^(127\.|10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|0\.|"
    r"169\.254\.|::1|localhost|0\.0\.0\.0)$"
)

def validate_url(url: str) -> str:
    """Validate URL is well-formed and not an internal address (SSRF protection)."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported scheme: {parsed.scheme}")
    host = parsed.hostname or ""
    if _BLOCKED_HOSTS.match(host):
        raise ValueError(f"Blocked internal address: {host}")
    return url


def fetch_with_requests(url: str) -> str:
    """Simple fetch using requests library."""
    validate_url(url)
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def fetch_with_playwright(url: str) -> str:
    """Fetch JS-rendered pages using Playwright + Chromium."""
    url_lower = url.lower()
    is_amazon = "amazon." in url_lower
    is_flipkart = "flipkart." in url_lower
    # Amazon & Flipkart never reach networkidle — use 'load' + scroll instead
    needs_scroll = is_amazon or is_flipkart
    wait_strategy = "load" if needs_scroll else "networkidle"
    timeout = 60000 if needs_scroll else 30000

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.goto(url, timeout=timeout, wait_until=wait_strategy)

        if needs_scroll:
            # Progressive scroll to trigger all lazy-loaded content
            for step in range(1, 6):
                page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {step} / 5)")
                page.wait_for_timeout(1500)
            # Scroll back to top so page finalizes layout
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)

        html = page.content()
        browser.close()
        return html


def _probe_page(url: str) -> tuple[str | None, bool]:
    """
    Fetch page with requests and determine if Playwright is needed.
    Returns (html_or_None, needs_playwright_bool).
    Reusing the probe response avoids a second HTTP round-trip.
    """
    from app.detectors.page_detector import JS_HEAVY_INDICATORS
    from bs4 import BeautifulSoup

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        html = response.text

        for indicator in JS_HEAVY_INDICATORS:
            if indicator in html:
                return None, True

        soup = BeautifulSoup(html, "lxml")
        if len(soup.get_text(strip=True)) < 200:
            return None, True

        return html, False

    except Exception:
        logger.warning("Probe fetch failed for %s — falling back to Playwright", url)
        return None, True


def smart_fetch(url: str, force_playwright: bool = False) -> dict:
    """
    Decide whether to use requests or Playwright,
    fetch the page (reusing the probe response when possible),
    and return html + method used.
    """
    from app.detectors.page_detector import detect_page_type

    # Always use Playwright for Amazon & Flipkart (JS SPAs)
    if force_playwright or "amazon." in url.lower() or "flipkart." in url.lower():
        html = fetch_with_playwright(url)
        method = "playwright"
    else:
        probed_html, use_playwright = _probe_page(url)
        if use_playwright:
            html = fetch_with_playwright(url)
            method = "playwright"
        else:
            html = probed_html
            method = "requests"

    page_type = detect_page_type(html, url)

    return {
        "html": html,
        "raw_html": html,   # expose for Amazon extractor
        "method": method,
        "page_type": page_type,
        "url": url
    }