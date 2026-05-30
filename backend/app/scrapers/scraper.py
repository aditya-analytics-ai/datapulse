from app.detectors.fetcher import smart_fetch
from app.scrapers.table_extractor import extract_tables
from app.scrapers.article_extractor import extract_article
from app.scrapers.json_extractor import extract_json
from app.scrapers.pdf_extractor import extract_pdf
from app.scrapers.amazon_extractor import extract_amazon_products
from app.scrapers.flipkart_extractor import extract_flipkart_products
from app.scrapers.product_extractor import extract_products
from app.scrapers.jsonld_extractor import extract_jsonld
from app.scrapers.linkedin_extractor import extract_linkedin_jobs
from app.cleaners.cleaner import clean_scraped_data

def run_scraper(url: str, force_playwright: bool = False) -> dict:
    """
    Main scraper function. Detects page type, extracts data,
    cleans it, and returns structured result.
    """

    # PDF handled separately
    if url.lower().endswith(".pdf"):
        raw_data = extract_pdf(url)
        cleaned = clean_scraped_data("pdf", raw_data)
        return {
            "url": url,
            "method": "pdfplumber",
            "page_type": "pdf",
            "raw_data": raw_data,
            "cleaned_data": cleaned
        }

    # Fetch the page
    fetched = smart_fetch(url, force_playwright)
    html = fetched["html"]
    method = fetched["method"]
    page_type = fetched["page_type"]

    # Extract
    if page_type == "table":
        raw_data = extract_tables(html)
    elif page_type == "json":
        raw_data = extract_json(html, url)
    elif page_type == "amazon_products":
        raw_data = extract_amazon_products(html, url)
    elif page_type == "flipkart_products":
        raw_data = extract_flipkart_products(html, url)
    elif page_type == "products":
        raw_data = extract_products(html, url)
    elif page_type == "jsonld":
        raw_data = extract_jsonld(html, url)
    elif page_type == "linkedin_jobs":
        raw_data = extract_linkedin_jobs(html, url)
    else:
        raw_data = extract_article(html, url)

    # Clean
    cleaned = clean_scraped_data(page_type, raw_data)

    return {
        "url": url,
        "method": method,
        "page_type": page_type,
        "raw_html": html,
        "raw_data": raw_data,
        "cleaned_data": cleaned
    }