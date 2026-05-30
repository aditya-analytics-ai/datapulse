"""
Amazon product extractor — parses search results, deals and listing pages
into structured rows: name, price, rating, reviews, url, asin.
Uses multiple selector strategies to maximise product count.
"""
from bs4 import BeautifulSoup
import re


def is_amazon_url(url: str) -> bool:
    return "amazon." in url.lower()


# Prefixes that pollute product names on deals/search pages
# Supports INR (₹), USD ($), GBP (£), EUR (€), etc.
_CURRENCY_SYMBOL = r"[\u20b9\$£€¥₩₽₹]"
_NOISE_PREFIXES = re.compile(
    rf"^(\d+%\s*off|ends in[\d:\s]+|deal price[:\s{_CURRENCY_SYMBOL}\d.,]+|m\.r\.p[:\s{_CURRENCY_SYMBOL}\d.,]+|"
    rf"limited time deal|sponsored|great indian festival|{_CURRENCY_SYMBOL}[\d,.]+\s*(m\.r\.p)?|"
    r"\d+:\d+:\d+|\d+\s*hrs?|today'?s deal|lightning deal)+",
    re.IGNORECASE,
)

def _clean_name(text: str) -> str:
    """Strip deal/price noise from the front of a product name."""
    cleaned = _NOISE_PREFIXES.sub("", text).strip()
    # If result is too short, the original might already be clean
    return cleaned if len(cleaned) > 8 else text


def extract_amazon_products(html: str, base_url: str = "") -> dict:
    """
    Parse Amazon search/listing/deals page HTML into structured product rows.
    Tries multiple selector strategies in order of preference.
    """
    soup = BeautifulSoup(html, "lxml")
    products = []

    # Strategy 1: standard search result cards
    cards = soup.select('[data-component-type="s-search-result"]')

    # Strategy 2: deal cards (Amazon Deals page)
    if len(cards) < 3:
        cards = soup.select('[data-testid="deal-card"]')

    # Strategy 3: any div/li with data-asin
    if len(cards) < 3:
        cards = [c for c in soup.select('[data-asin]')
                 if c.get('data-asin', '').strip() and c.name in ('div', 'li')]

    # Strategy 4: s-result-item
    if len(cards) < 3:
        cards = soup.select('.s-result-item[data-asin]')

    for card in cards:
        try:
            product = _parse_card(card, base_url)
            if product.get("name") and len(product["name"]) > 5:
                products.append(product)
        except Exception:
            continue

    # Remove duplicates by ASIN or name prefix
    products = _dedupe(products)

    # Fallback: parse raw anchor links
    if len(products) < 3:
        products = _link_fallback(soup, base_url)

    return {
        "page_type": "amazon_products",
        "source": base_url,
        "total": len(products),
        "columns": ["name", "price", "original_price", "discount", "rating", "reviews", "asin", "url"],
        "products": products
    }


def _parse_card(card, base_url: str) -> dict:
    name = ""

    # Priority 1: image alt text — Amazon ALWAYS puts product name here
    for img in card.select('img[alt]'):
        alt = img.get('alt', '').strip()
        if len(alt) > 10 and not re.match(r'^[\d%\s:]+$', alt):
            name = alt[:200]
            break

    # Priority 2: aria-label on anchor links
    if not name:
        for a in card.select('a[aria-label]'):
            lbl = a.get('aria-label', '').strip()
            if len(lbl) > 10:
                name = _clean_name(lbl)[:200]
                break

    # Priority 3: specific text selectors
    if not name:
        for sel in [
            "h2 a span",
            "[data-cy='title-recipe'] span",
            "h2 span.a-text-normal",
            "h2 span",
            ".a-text-normal",
            ".a-size-base-plus",
            ".a-size-medium",
            "[data-testid='deal-title']",
            ".DealContent-module__truncate",
            "span[class*='title']",
            "div[class*='title']",
        ]:
            el = card.select_one(sel)
            if el:
                txt = el.get_text(strip=True)
                if len(txt) > 8:
                    name = _clean_name(txt)
                    break

    # Priority 4: full container text, find largest non-noise segment
    if not name or len(name) < 8:
        full_text = card.get_text(separator=" ", strip=True)
        segments = re.split(rf'{_CURRENCY_SYMBOL}[\d,]+|M\.R\.P|Deal Price|% off|Ends in|Limited time', full_text)
        for seg in reversed(segments):
            seg = seg.strip()
            if len(seg) > 15 and not re.match(rf'^[\d\s,.{_CURRENCY_SYMBOL}%:]+$', seg):
                name = seg[:200]
                break

    # Price
    price = ""
    for sel in [".a-price .a-offscreen", ".a-price-whole",
                "[data-testid='deal-price']", ".DealPrice"]:
        el = card.select_one(sel)
        if el:
            price = el.get_text(strip=True).replace("\xa0", "").strip()
            break

    # Original / MRP
    original_price = ""
    el = card.select_one(".a-text-price .a-offscreen")
    if el:
        original_price = el.get_text(strip=True).replace("\xa0", "").strip()

    # Discount badge
    discount = ""
    for sel in [".a-badge-text", "[data-a-badge-type] .a-badge-text",
                ".s-coupon-unclipped", "[data-testid='discount-badge']"]:
        el = card.select_one(sel)
        if el:
            discount = el.get_text(strip=True)
            break

    # Rating
    rating = ""
    for sel in [".a-icon-star-small .a-icon-alt", ".a-icon-alt"]:
        el = card.select_one(sel)
        if el:
            m = re.search(r"[\d.]+", el.get_text(strip=True))
            if m:
                rating = m.group()
                break

    # Review count
    reviews = ""
    for sel in ['[aria-label*="ratings"]', '[aria-label*="stars"]', ".s-underline-text"]:
        el = card.select_one(sel)
        if el:
            aria = el.get("aria-label", "")
            m = re.search(r"[\d,]+", aria if aria else el.get_text())
            if m:
                reviews = m.group().replace(",", "")
                break

    # ASIN
    asin = card.get("data-asin", "")

    # URL
    url = _extract_url(card, base_url)

    return {
        "name": name,
        "price": price,
        "original_price": original_price,
        "discount": discount,
        "rating": rating,
        "reviews": reviews,
        "asin": asin,
        "url": url,
    }


def _extract_url(card, base_url: str) -> str:
    for sel in ["h2 a", "a.a-link-normal[href*='/dp/']", "a.a-link-normal", "a[href*='/dp/']"]:
        el = card.select_one(sel)
        if el and el.get("href"):
            href = el["href"]
            if href.startswith("/"):
                m = re.match(r"https?://[^/]+", base_url)
                domain = m.group() if m else "https://www.amazon.com"
                return domain + href
            elif href.startswith("http"):
                return href
    return ""


def _dedupe(products: list) -> list:
    seen = set()
    unique = []
    for p in products:
        key = p.get("asin") or p.get("name", "")[:40]
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def _link_fallback(soup: BeautifulSoup, base_url: str) -> list:
    """
    Last resort: extract product info from anchor links that contain /dp/ ASIN paths.
    Tries to parse price from surrounding text.
    """
    results = []
    seen_asins = set()

    for a in soup.select("a[href*='/dp/']"):
        href = a.get("href", "")
        asin_m = re.search(r"/dp/([A-Z0-9]{10})", href)
        if not asin_m:
            continue
        asin = asin_m.group(1)
        if asin in seen_asins:
            continue
        seen_asins.add(asin)

        # Get text from this link or its parent
        raw_text = a.get_text(separator=" ", strip=True)

        # Try to extract a clean name — look for text that isn't price/deal noise
        name = _clean_name(raw_text)
        if len(name) < 10:
            # Try parent element for more context
            parent = a.parent
            if parent:
                raw_text = parent.get_text(separator=" ", strip=True)
                name = _clean_name(raw_text)

        if len(name) < 10:
            continue

        # Try to find price in nearby text (support multiple currencies)
        price = ""
        price_m = re.search(rf"{_CURRENCY_SYMBOL}[\d,]+", raw_text)
        if price_m:
            price = price_m.group()

        # Build URL
        if href.startswith("/"):
            m = re.match(r"https?://[^/]+", base_url)
            domain = m.group() if m else "https://www.amazon.com"
            url = domain + href
        else:
            url = href

        results.append({
            "name": name[:200],   # cap length
            "price": price,
            "original_price": "",
            "discount": "",
            "rating": "",
            "reviews": "",
            "asin": asin,
            "url": url,
        })

        if len(results) >= 200:
            break

    return results
