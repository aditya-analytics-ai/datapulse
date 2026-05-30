"""
Generic Schema.org / JSON-LD extractor.
Parses <script type="application/ld+json"> blocks that many modern sites embed.
Works for Product, JobPosting, Article, Recipe, Event, and more.
"""
from bs4 import BeautifulSoup
import json
import re


def extract_jsonld(html: str, url: str = "") -> dict:
    """
    Extract all JSON-LD blocks from HTML and normalize them.
    Returns structured data grouped by schema type.
    """
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script", type="application/ld+json")
    if not scripts:
        return {"page_type": "jsonld", "found": False, "items": []}

    items = []
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    normalized = _normalize(item)
                    if normalized:
                        items.append(normalized)
            else:
                normalized = _normalize(data)
                if normalized:
                    items.append(normalized)
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    return {
        "page_type": "jsonld",
        "found": len(items) > 0,
        "source_url": url,
        "total": len(items),
        "items": items,
    }


_SCHEMA_PRIORITY = {
    "Product": "product",
    "JobPosting": "job",
    "Article": "article",
    "NewsArticle": "article",
    "Recipe": "recipe",
    "Event": "event",
    "LocalBusiness": "business",
    "Organization": "organization",
    "Person": "person",
    "Review": "review",
    "FAQPage": "faq",
    "Course": "course",
    "ProductModel": "product",
}


def _normalize(item: dict) -> dict | None:
    """Flatten a JSON-LD item into a consistent dict."""
    if not isinstance(item, dict):
        return None

    type_name = ""
    atype = item.get("@type", "")
    if isinstance(atype, list):
        # Pick the most specific type
        for t in atype:
            if t in _SCHEMA_PRIORITY:
                type_name = t
                break
        if not type_name and atype:
            type_name = atype[0]
    else:
        type_name = atype

    category = _SCHEMA_PRIORITY.get(type_name, "other")

    result = {
        "@type": type_name,
        "category": category,
        "name": _get_text(item, "name"),
        "description": _get_text(item, "description"),
        "url": _get_text(item, "url"),
        "image": _get_image(item),
    }

    if category == "product":
        result.update(_extract_product(item))
    elif category == "job":
        result.update(_extract_job(item))
    elif category == "article":
        result.update(_extract_article(item))
    elif category == "recipe":
        result.update(_extract_recipe(item))
    elif category == "event":
        result.update(_extract_event(item))
    elif category == "faq":
        result.update(_extract_faq(item))

    return result


def _get_text(item: dict, key: str) -> str:
    val = item.get(key, "")
    if isinstance(val, dict):
        return val.get("text", "")
    if isinstance(val, list):
        return " ".join(str(v) for v in val if isinstance(v, str))
    return str(val) if val else ""


def _get_image(item: dict) -> str:
    img = item.get("image", "")
    if isinstance(img, dict):
        return img.get("url", "")
    if isinstance(img, list) and img:
        first = img[0]
        if isinstance(first, dict):
            return first.get("url", "")
        return str(first)
    return str(img) if img else ""


def _extract_product(item: dict) -> dict:
    offers = item.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    price = offers.get("price", "") if isinstance(offers, dict) else ""
    currency = offers.get("priceCurrency", "") if isinstance(offers, dict) else ""
    availability = offers.get("availability", "") if isinstance(offers, dict) else ""
    if isinstance(availability, str):
        availability = availability.rstrip("/").split("/")[-1] if "/" in availability else availability

    return {
        "price": str(price) if price else "",
        "currency": currency,
        "availability": availability,
        "sku": item.get("sku", ""),
        "brand": _get_text(item.get("brand", {}), "name") if isinstance(item.get("brand"), dict) else "",
        "rating": _get_rating(item),
    }


def _get_rating(item: dict) -> dict:
    agg = item.get("aggregateRating", {})
    if isinstance(agg, dict):
        return {
            "rating_value": agg.get("ratingValue", ""),
            "review_count": agg.get("reviewCount", ""),
            "best_rating": agg.get("bestRating", ""),
        }
    return {"rating_value": "", "review_count": "", "best_rating": ""}


def _extract_job(item: dict) -> dict:
    return {
        "job_title": item.get("title", ""),
        "hiring_organization": _get_text(item.get("hiringOrganization", {}), "name") if isinstance(item.get("hiringOrganization"), dict) else "",
        "location": _get_location(item.get("jobLocation")),
        "salary": _get_salary(item),
        "employment_type": item.get("employmentType", ""),
        "date_posted": item.get("datePosted", ""),
        "valid_through": item.get("validThrough", ""),
    }


def _get_location(loc) -> str:
    if isinstance(loc, dict):
        return loc.get("address", {}).get("addressLocality", "") if isinstance(loc.get("address"), dict) else ""
    if isinstance(loc, list):
        parts = []
        for l in loc:
            if isinstance(l, dict):
                a = l.get("address", {})
                if isinstance(a, dict) and a.get("addressLocality"):
                    parts.append(a["addressLocality"])
        return ", ".join(parts)
    return ""


def _get_salary(item: dict) -> str:
    base = item.get("baseSalary", {})
    if isinstance(base, dict):
        val = base.get("value", {})
        if isinstance(val, dict):
            return f"{val.get('value', '')} {val.get('currency', '')}".strip()
    return ""


def _extract_article(item: dict) -> dict:
    return {
        "headline": item.get("headline", ""),
        "author": _get_text(item.get("author", {}), "name") if isinstance(item.get("author"), dict) else "",
        "date_published": item.get("datePublished", ""),
        "date_modified": item.get("dateModified", ""),
        "publisher": _get_text(item.get("publisher", {}), "name") if isinstance(item.get("publisher"), dict) else "",
    }


def _extract_recipe(item: dict) -> dict:
    return {
        "cook_time": item.get("cookTime", ""),
        "prep_time": item.get("prepTime", ""),
        "total_time": item.get("totalTime", ""),
        "recipe_yield": item.get("recipeYield", ""),
        "calories": _get_text(item.get("nutrition", {}), "calories") if isinstance(item.get("nutrition"), dict) else "",
        "ingredients": item.get("recipeIngredient", []),
        "instructions": _get_instructions(item),
    }


def _get_instructions(item: dict) -> list:
    instr = item.get("recipeInstructions", [])
    if isinstance(instr, list):
        steps = []
        for s in instr:
            if isinstance(s, dict):
                steps.append(s.get("text", ""))
            elif isinstance(s, str):
                steps.append(s)
        return steps
    return []


def _extract_event(item: dict) -> dict:
    return {
        "start_date": item.get("startDate", ""),
        "end_date": item.get("endDate", ""),
        "location": _get_location(item.get("location")),
        "event_status": item.get("eventStatus", ""),
        "performer": _get_text(item.get("performer", {}), "name") if isinstance(item.get("performer"), dict) else "",
    }


def _extract_faq(item: dict) -> dict:
    questions = []
    main_entity = item.get("mainEntity", [])
    if isinstance(main_entity, list):
        for entry in main_entity:
            if isinstance(entry, dict) and entry.get("@type") == "Question":
                questions.append({
                    "question": entry.get("name", ""),
                    "answer": _get_text(entry.get("acceptedAnswer", {}), "text") if isinstance(entry.get("acceptedAnswer"), dict) else "",
                })
    return {"questions": questions}
