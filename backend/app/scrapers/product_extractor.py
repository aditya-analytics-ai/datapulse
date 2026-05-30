"""
Generic product/e-commerce extractor.
Detects product cards on any e-commerce site by looking for
common patterns: price indicators, product images, rating stars,
add-to-cart buttons, and structured data attributes.
Works on Flipkart, Myntra, Ajio, Snapdeal, and similar sites.
"""
from bs4 import BeautifulSoup
import re


_CURRENCY_RE = re.compile(r"[\u20b9\$£€¥₩₽₹,.\d]+")
_PRICE_SYMBOLS = r"[\u20b9\$£€¥₩₽₹]"
_PRODUCT_CARD_SELECTORS = [
    "[data-testid*='product' i]",
    "[data-testid*='card' i]",
    "[data-testid*='item' i]",
    "[class*='product' i]",
    "[class*='card' i]",
    "[class*='item' i]",
    "[class*='grid' i]",
    "li[class*='product']",
    "div[class*='offer']",
    "div[class*='deal']",
]

_PRICE_SELECTORS = [
    "[class*='price' i]",
    "[class*='rate' i]",
    "[class*='cost' i]",
    "[class*='amount' i]",
    "[data-testid*='price' i]",
    "span[class*='offer' i]",
]


def extract_products(html: str, base_url: str = "") -> dict:
    """
    Parse any e-commerce page into structured product rows.
    Works by finding product-like card elements, then extracting
    name, price, rating, image from each.
    """
    soup = BeautifulSoup(html, "lxml")
    products = []

    cards = _find_product_cards(soup)

    for card in cards:
        try:
            product = _parse_product_card(card, base_url)
            if product.get("name") and len(product["name"]) > 5:
                products.append(product)
        except Exception:
            continue

    products = _dedupe(products)

    return {
        "page_type": "products",
        "source": base_url,
        "total": len(products),
        "columns": ["name", "price", "original_price", "discount", "rating", "reviews", "url"],
        "products": products,
    }


def _find_product_cards(soup: BeautifulSoup) -> list:
    """Find elements that look like product cards."""
    candidates = []

    for sel in _PRODUCT_CARD_SELECTORS:
        found = soup.select(sel)
        if found:
            candidates.extend(found)

    # Try to find repeating pattern: sibling divs/sections with images + prices
    if len(candidates) < 3:
        for container in soup.find_all(["div", "section", "ul", "ol"]):
            children = container.find_all(["div", "li"], recursive=False)
            price_children = [
                c for c in children
                if c.find(["span", "div", "p"], string=_PRICE_SYMBOLS)
            ]
            if len(price_children) > 2:
                candidates = price_children
                break

    # Try any list items with images
    if len(candidates) < 3:
        for li in soup.find_all("li"):
            if li.find("img") and (li.find(["span", "div"], string=_PRICE_SYMBOLS) or re.search(_PRICE_SYMBOLS, li.get_text())):
                candidates.append(li)

    return candidates[:100]


def _parse_product_card(card, base_url: str) -> dict:
    """Extract name, price, rating, image from a single product card."""
    name = _extract_name(card)
    price = _extract_price(card)
    original_price = _extract_original_price(card)
    discount = _extract_discount(card)
    rating = _extract_rating(card)
    reviews = _extract_reviews(card)
    url = _extract_url(card, base_url)
    image = _extract_image(card)

    return {
        "name": name,
        "price": price,
        "original_price": original_price,
        "discount": discount,
        "rating": rating,
        "reviews": reviews,
        "url": url,
        "image": image,
    }


def _extract_name(card) -> str:
    # Priority 1: image alt text
    for img in card.select("img[alt]"):
        alt = img.get("alt", "").strip()
        if len(alt) > 10:
            return alt[:200]

    # Priority 2: link aria-label
    for a in card.select("a[aria-label]"):
        lbl = a.get("aria-label", "").strip()
        if len(lbl) > 10:
            return lbl[:200]

    # Priority 3: common heading class patterns
    for sel in [
        "a[class*='name' i]",
        "a[class*='title' i]",
        "span[class*='name' i]",
        "span[class*='title' i]",
        "div[class*='name' i]",
        "div[class*='title' i]",
        "h1",
        "h2",
        "h3",
        "a[href*='product']",
        "a[href*='pdp']",
        "a[href*='item']",
    ]:
        el = card.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            if len(txt) > 8:
                return txt[:200]

    # Priority 4: largest text in card (likely the product name)
    texts = sorted(card.find_all(string=True), key=lambda x: len(x.strip()), reverse=True)
    for t in texts:
        t = t.strip()
        if len(t) > 15 and not re.match(rf"^[\d\s,.{_PRICE_SYMBOLS}%:]+$", t):
            return t[:200]

    return ""


def _extract_price(card) -> str:
    for sel in _PRICE_SELECTORS:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(rf"{_PRICE_SYMBOLS}\s*[\d,]+(?:\.\d+)?", text)
            if m:
                return m.group()
    # Fallback: scan text for price pattern
    text = card.get_text()
    m = re.search(rf"{_PRICE_SYMBOLS}\s*[\d,]+(?:\.\d+)?", text)
    if m:
        return m.group()
    return ""


def _extract_original_price(card) -> str:
    for sel in [
        "[class*='original' i]",
        "[class*='old' i]",
        "[class*='mrp' i]",
        "[class*='strike' i]",
        "[class*='cut' i]",
        "del",
        "s",
    ]:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(rf"{_PRICE_SYMBOLS}\s*[\d,]+(?:\.\d+)?", text)
            if m:
                return m.group()
    return ""


def _extract_discount(card) -> str:
    for sel in [
        "[class*='discount' i]",
        "[class*='offer' i]",
        "[class*='off' i]",
        "[class*='save' i]",
        "[class*='badge' i]",
    ]:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"\d+\s*%", text)
            if m:
                return m.group()
    return ""


def _extract_rating(card) -> str:
    for sel in [
        "[class*='rating' i]",
        "[class*='star' i]",
        "[data-testid*='rating' i]",
        "span[class*='rate']",
        "div[class*='rate']",
    ]:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"[\d.]+", text)
            if m:
                return m.group()
    return ""


def _extract_reviews(card) -> str:
    for sel in [
        "[class*='review' i]",
        "[data-testid*='review' i]",
        "span[class*='rating-count']",
    ]:
        el = card.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"[\d,]+", text)
            if m:
                return m.group().replace(",", "")
    return ""


def _extract_url(card, base_url: str) -> str:
    for sel in ["a[href]", "h2 a", "h3 a", "a[class*='link' i]"]:
        el = card.select_one(sel) if sel != "a[href]" else card.find("a", href=True)
        if sel == "a[href]":
            el = card.find("a", href=True)
        else:
            el = card.select_one(sel)
        if el and el.get("href"):
            href = el["href"]
            if href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                domain = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
                return domain + href if domain else href
            elif href.startswith("http"):
                return href
    return ""


def _extract_image(card) -> str:
    for img in card.select("img[src]"):
        src = img.get("src", "")
        if src.startswith("http") and "icon" not in src.lower():
            return src
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
