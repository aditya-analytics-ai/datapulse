import requests
from bs4 import BeautifulSoup

JS_HEAVY_INDICATORS = [
    "__NEXT_DATA__",
    "ng-version",
    "data-reactroot",
    "__nuxt",
    "window.__INITIAL_STATE__",
    "window.__APP__",
]

def needs_playwright(url: str) -> bool:
    """
    Quickly fetch the page with requests and check if it
    looks like a JS-rendered site. If yes, we use Playwright.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text

        # Check for JS framework fingerprints
        for indicator in JS_HEAVY_INDICATORS:
            if indicator in html:
                return True

        # Check if page body is nearly empty (JS hasn't rendered yet)
        soup = BeautifulSoup(html, "lxml")
        body_text = soup.get_text(strip=True)
        if len(body_text) < 200:
            return True

        return False

    except Exception:
        # If request fails, try Playwright
        return True


def detect_page_type(html: str, url: str) -> str:
    """
    Given raw HTML, detect what kind of data the page contains.
    Returns: 'table' | 'article' | 'json' | 'pdf' | 'amazon_products'
    """

    # Amazon product pages — must check before anything else
    if "amazon." in url.lower():
        return "amazon_products"

    # PDF check
    if url.lower().endswith(".pdf"):
        return "pdf"

    # JSON check
    if url.lower().endswith(".json"):
        return "json"
    try:
        stripped = html.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return "json"
    except Exception:
        pass

    # HTML table check
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    if tables:
        # Make sure the table has actual data rows
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) >= 3:
                return "table"

    # Article / text check
    article_tags = soup.find_all(["article", "main", "section"])
    if article_tags:
        return "article"

    # Fallback — treat as article if there's a lot of text
    body_text = soup.get_text(strip=True)
    if len(body_text) > 300:
        return "article"

    return "article"