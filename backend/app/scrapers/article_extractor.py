from bs4 import BeautifulSoup

def extract_article(html: str, url: str = "") -> dict:
    """
    Extract structured content from article/text pages.
    Returns title, text, links, images, metadata.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove junk tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    # Title
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)

    # Meta description
    description = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        description = meta.get("content", "")

    # Main text content
    # Try article/main tags first, fallback to body
    content_tag = (
        soup.find("article") or
        soup.find("main") or
        soup.find("div", class_=lambda c: c and "content" in c.lower()) or
        soup.find("body")
    )

    paragraphs = []
    if content_tag:
        for p in content_tag.find_all(["p", "li", "h1", "h2", "h3", "h4"]):
            text = p.get_text(strip=True)
            if len(text) > 30:
                paragraphs.append(text)

    full_text = "\n".join(paragraphs)

    # Headings
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]

    # Links
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if href.startswith("http") and text:
            links.append({"text": text, "url": href})

    # Images
    images = []
    for img in soup.find_all("img", src=True):
        src = img.get("src", "")
        alt = img.get("alt", "")
        if src.startswith("http"):
            images.append({"src": src, "alt": alt})

    return {
        "title": title,
        "description": description,
        "headings": headings[:10],
        "paragraphs": paragraphs,
        "full_text": full_text[:5000],
        "links": links[:20],
        "images": images[:10],
        "word_count": len(full_text.split()),
        "url": url
    }