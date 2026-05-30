"""
Flipkart-specific product extractor.
Parses search, category, and product listing pages on Flipkart
into structured rows: name, price, original_price, discount, rating, reviews, url.
Uses Flipkart's specific DOM structure and CSS classes.
"""
from bs4 import BeautifulSoup
import re


def is_flipkart_url(url: str) -> bool:
    return "flipkart." in url.lower()


def extract_flipkart_products(html: str, base_url: str = "") -> dict:
    """
    Parse Flipkart search/listing page HTML into structured product rows.
    """
    soup = BeautifulSoup(html, "lxml")
    products = []

    # Strategy 1: modern Flipkart — row container with product data
    cards = soup.select("[data-tkid]")
    # Strategy 2: older Flipkart — specific class patterns
    if len(cards) < 3:
        cards = soup.select("._1xHGtK, ._2kHMtA, ._1AtVbE, ._13oc-S, div[class*='_2kHM']")
    # Strategy 3: any div with product-like structure
    if len(cards) < 3:
        cards = soup.select("div[style*='flex'] a[href*='p/']")
    # Strategy 4: link-based fallback
    if len(cards) < 3:
        cards = _find_product_slots(soup)

    for card in cards:
        try:
            product = _parse_card(card, base_url)
            if product.get("name") and len(product["name"]) > 5:
                products.append(product)
        except Exception:
            continue

    # Deduplicate by name
    products = _dedupe(products)

    # Link fallback if still empty
    if len(products) < 3:
        products = _link_fallback(soup, base_url)

    return {
        "page_type": "flipkart_products",
        "source": base_url,
        "total": len(products),
        "columns": ["name", "price", "original_price", "discount", "rating", "reviews", "url"],
        "products": products,
    }


def _find_product_slots(soup: BeautifulSoup) -> list:
    """Find repeated product-like elements in the DOM."""
    # Look for divs containing price pattern + image + link
    candidates = []
    for div in soup.find_all("div"):
        if not div.get("id") and not div.get("class"):
            continue
        text = div.get_text(strip=True)[:200]
        if re.search(r"[\u20b9\$]\s*[\d,]+", text) and div.find("a", href=True) and div.find("img"):
            candidates.append(div)
    # Pick the ones with most siblings (likely a grid)
    return candidates[:60]


def _parse_card(card, base_url: str) -> dict:
    # Collect text from next siblings — Flipkart often places
    # rating/review info outside the data-tkid element
    siblings_parts = []
    for sib in card.find_next_siblings():
        sib_text = sib.get_text(strip=True)
        if not sib_text:
            continue  # skip empty spacers
        if len(sib_text) >= 300:
            break     # probably a different product, stop
        siblings_parts.append(sib_text)
    siblings_text = " ".join(siblings_parts)

    name = _extract_name(card)
    price = _extract_price(card)
    original_price = _extract_original_price(card)
    discount = _extract_discount(card)
    rating = _extract_rating(card, siblings_text)
    reviews = _extract_reviews(card, siblings_text)
    url = _extract_url(card, base_url)

    return {
        "name": name,
        "price": price,
        "original_price": original_price,
        "discount": discount,
        "rating": rating,
        "reviews": reviews,
        "url": url,
    }


_FLIPKART_NAME_SELECTORS = [
    "a[class*='IRpwTa' i]",       # modern FK
    "a[class*='s1Q9rs' i]",       # modern FK
    "._4rR01T",                   # older FK product name
    "a[href*='p/'] img[alt]",     # image alt
    "img[alt][src*='flipkart']",
    "a[class*='title' i]",
    "span[class*='name' i]",
    "div[class*='name' i]",
    "div[class*='title' i]",
    "h2 a",
    "h3 a",
    "a[class*='product' i]",
]


def _extract_name(card) -> str:
    # Priority 1: image alt text
    for img in card.select("img[alt]"):
        alt = img.get("alt", "").strip()
        if len(alt) > 10:
            return alt[:200]

    # Priority 2: known FK selectors
    for sel in _FLIPKART_NAME_SELECTORS:
        el = card.select_one(sel)
        if el and el.name == "img":
            alt = el.get("alt", "").strip()
            if len(alt) > 10:
                return alt[:200]
        elif el:
            txt = el.get_text(strip=True)
            if len(txt) > 8:
                return txt[:200]

    # Priority 3: links with product-like href
    for a in card.select("a[href*='p/']"):
        txt = a.get_text(strip=True)
        if len(txt) > 8:
            return txt[:200]

    return ""


_FLIPKART_PRICE_SELECTORS = [
    "._30jeq3",                     # FK current price class
    "div[class*='price' i]",
    "span[class*='price' i]",
    "[class*='amount' i]",
    "[data-testid*='price' i]",
]


def _extract_price(card) -> str:
    for sel in _FLIPKART_PRICE_SELECTORS:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"[\u20b9\$]\s*[\d,]+(?:\.\d+)?", text)
            if m:
                return m.group()
    # Fallback
    text = card.get_text()
    m = re.search(r"[\u20b9\$]\s*[\d,]+(?:\.\d+)?", text)
    if m:
        return m.group()
    return ""


def _extract_original_price(card) -> str:
    for sel in [
        "._3I9_wc",                    # FK old/mrp price
        "[class*='old' i]",
        "[class*='mrp' i]",
        "[class*='strike' i]",
        "del",
        "s",
    ]:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"[\u20b9\$]\s*[\d,]+(?:\.\d+)?", text)
            if m:
                return m.group()
    return ""


def _extract_discount(card) -> str:
    for sel in [
        "._3Ay6Sb",                    # FK discount
        "[class*='discount' i]",
        "[class*='offer' i]",
        "span[class*='badge' i]",
    ]:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"(\d{1,2})\s*%", text)
            if m:
                return f"{m.group(1)}% off"
    # Fallback: scan card text for realistic discount patterns
    text = card.get_text()
    m = re.search(r"(\d{1,2})\s*%\s*(off|discount)", text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}% off"
    return ""


def _extract_rating(card, extra_text: str = "") -> str:
    for sel in [
        "._3LWZlK",                    # FK rating
        "[class*='rating' i]",
        "[class*='star' i]",
        "span[class*='rate']",
    ]:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"([\d.]+)", text)
            if m:
                val = m.group(1)
                try:
                    if 1 <= float(val) <= 5:
                        return val
                except ValueError:
                    pass
    # Try text patterns on card + siblings text
    text = card.get_text() + " " + extra_text
    patterns = [
        r"([\d.]+)\s*[★☆⭐]",         # "4.2★" "4★"
        r"[★☆⭐]\s*([\d.]+)",         # "★4.2"
        r"(?:rating|ratings|score)[: ]*([\d.]+)",  # "rating 4.2"
        r"([\d.]+)\s*/\s*5",           # "4.2/5"
        r"([\d.]+)\s*out\s*of\s*5",    # "4.2 out of 5"
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1)
            try:
                f = float(val)
                if 1 <= f <= 5:
                    return val
            except ValueError:
                pass
    # Standalone decimal between 1-5
    m = re.search(r"\b([1-5]\.[0-9])\b", text)
    if m:
        return m.group(1)
    # Direct star search: find the element containing ★ and extract nearby number
    star_el = card.find(string=re.compile(r"[★☆⭐]"))
    if star_el:
        container = star_el.parent
        if container:
            ctx2 = " ".join(t for t in container.stripped_strings)
            m = re.search(r"([\d.]+)", ctx2)
            if m:
                val = m.group(1)
                try:
                    if 1 <= float(val) <= 5:
                        return val
                except ValueError:
                    pass
    return ""


def _extract_reviews(card, extra_text: str = "") -> str:
    for sel in [
        "._2_R_DZ",                    # FK review count
        "span[class*='review' i]",
        "span[class*='rating-count' i]",
        "[data-testid*='review' i]",
        "[class*='rating' i] span",
    ]:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"[\d,]+", text)
            if m:
                return m.group().replace(",", "")
    # Fallback: scan card + siblings text for review/ratings count patterns
    text = card.get_text() + " " + extra_text
    patterns = [
        r"(?:ratings?|reviews?)\s*([\d,]+)",     # "ratings 88" "reviews 22"
        r"([\d,]+)\s*(?:ratings?|reviews?)",     # "88 ratings" "22 reviews"
        r"(?:\d\.?\d?\s*★?\s*)\(([\d,]+)\)",    # "4.2★ (88)" after rating number
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).replace(",", "")
    return ""


def _extract_url(card, base_url: str) -> str:
    for a in card.select("a[href]"):
        href = a.get("href", "")
        if "/p/" in href or "/product" in href:
            if href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                domain = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
                return domain + href
            elif href.startswith("http"):
                return href
    # Fallback: any link
    a = card.find("a", href=True)
    if a:
        href = a["href"]
        if href.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            domain = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
            return domain + href
        elif href.startswith("http"):
            return href
    return ""


def _dedupe(products: list) -> list:
    seen = set()
    unique = []
    for p in products:
        key = p.get("name", "")[:40]
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def _link_fallback(soup: BeautifulSoup, base_url: str) -> list:
    """Last resort: extract from anchor links with /p/ ASIN-like paths."""
    results = []
    seen = set()
    from urllib.parse import urlparse, urljoin

    for a in soup.select("a[href*='/p/']"):
        href = a.get("href", "")
        if not href:
            continue
        name = a.get_text(strip=True)
        if len(name) < 10:
            img = a.find("img")
            if img:
                name = img.get("alt", "").strip()
        if len(name) < 10:
            continue
        if name in seen:
            continue
        seen.add(name)

        full_url = ""
        if href.startswith("/"):
            parsed = urlparse(base_url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            full_url = domain + href
        elif href.startswith("http"):
            full_url = href

        # Look for price near this link
        parent = a.parent
        price = ""
        if parent:
            m = re.search(r"[\u20b9\$]\s*[\d,]+", parent.get_text())
            if m:
                price = m.group()

        results.append({
            "name": name[:200],
            "price": price,
            "original_price": "",
            "discount": "",
            "rating": "",
            "reviews": "",
            "url": full_url,
        })

        if len(results) >= 200:
            break

    return results
