from bs4 import BeautifulSoup
import re

# Exported so fetcher can import without re-defining
JS_HEAVY_INDICATORS = [
    "__NEXT_DATA__",
    "ng-version",
    "data-reactroot",
    "__nuxt",
    "window.__INITIAL_STATE__",
    "window.__APP__",
]


def detect_page_type(html: str, url: str) -> str:
    """
    Given raw HTML, detect what kind of data the page contains.
    Returns: 'table' | 'article' | 'json' | 'pdf' | 'amazon_products'
             | 'flipkart_products' | 'products' | 'jsonld'
    """

    # Site-specific checks — must be early
    if "amazon." in url.lower():
        return "amazon_products"
    if "flipkart." in url.lower():
        return "flipkart_products"
    if ("linkedin." in url.lower() or "linkedin.com" in url.lower()) and "/jobs" in url.lower():
        return "linkedin_jobs"

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

    soup = BeautifulSoup(html, "lxml")

    # JSON-LD check — many modern sites embed Schema.org data
    scripts = soup.find_all("script", type="application/ld+json")
    if scripts:
        import json as _json
        for script in scripts:
            try:
                data = _json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    atype = item.get("@type", "")
                    if isinstance(atype, list):
                        atype = atype[0]
                    if atype in ("Product", "JobPosting", "Article", "NewsArticle",
                                 "Recipe", "Event", "FAQPage", "LocalBusiness"):
                        return "jsonld"
            except Exception:
                continue

    # HTML table check
    tables = soup.find_all("table")
    if tables:
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) >= 3:
                return "table"

    # Generic e-commerce / product page detection
    if _looks_like_product_page(soup):
        return "products"

    # Article / text check
    article_tags = soup.find_all(["article", "main", "section"])
    if article_tags:
        return "article"

    # Fallback — treat as article if there's enough text
    body_text = soup.get_text(strip=True)
    if len(body_text) > 300:
        return "article"

    return "article"


def _looks_like_product_page(soup: BeautifulSoup) -> bool:
    """Heuristic: page has recurring patterns common on e-commerce sites."""
    text = soup.get_text()

    # Must have a price symbol somewhere
    if not re.search(r"[\u20b9\$£€¥₩]", text):
        return False

    # Check for multiple structured product-like elements
    score = 0

    # Multiple images with product-like alt text
    img_alts = [img.get("alt", "") for img in soup.select("img[alt]")]
    product_alts = [a for a in img_alts if len(a) > 10 and not re.match(r"^[\d\s%]+$", a)]
    if len(product_alts) > 5:
        score += 2

    # Multiple price-like patterns
    price_matches = re.findall(r"[\u20b9\$£€¥₩]\s*[\d,]+", text)
    if len(price_matches) > 3:
        score += 2

    # Rating stars or rating text
    if re.search(r"[\d.]+\s*(out of|stars?|rating)", text, re.IGNORECASE):
        score += 1
    if soup.select_one("[class*='star' i], [class*='rating' i]"):
        score += 1

    # Add to cart / buy now patterns
    if re.search(r"add to cart|buy now|add to bag|shop now", text, re.IGNORECASE):
        score += 1

    # Product grid / list structure
    if soup.select("[class*='product' i], [class*='grid' i], [class*='card' i]"):
        score += 1

    return score >= 3