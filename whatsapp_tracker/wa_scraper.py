"""
wa_scraper.py - Playwright-based WhatsApp Web message scraper.
No API needed. Uses saved browser session from first_run.py.
"""
import os, time, hashlib, base64, io
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SESSION_DIR = os.path.join(os.path.dirname(__file__), "wa_session")
WA_URL = "https://web.whatsapp.com"

_CHAT_LIST = ['[data-testid="chat-list"]', '#pane-side', '[aria-label="Chat list"]']
_MSG_TEXT  = [
    'div.copyable-text',                  # full message bubble (confirmed working)
    '[data-testid="msg-text"]',           # older WhatsApp versions
    '.selectable-text.copyable-text',
]
_MSG_IMAGE = [
    'img[src^="blob:"]',                  # WhatsApp blob images
    'img[src^="data:"]',                  # base64 images
    '[data-testid="msg-image"]',          # image message container
    'div[aria-label*="image"] img',       # accessible image label
]


def _wait_any(page, selectors, timeout=15_000):
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=timeout)
            return sel
        except PWTimeout:
            continue
    return None


def _download_image(page, img_locator) -> bytes | None:
    """Download image from WhatsApp Web (handles blob: and data: URLs)."""
    try:
        # Get the image source
        src = img_locator.get_attribute("src")
        if not src:
            return None

        if src.startswith("data:"):
            # Base64 encoded image
            header, data = src.split(",", 1)
            return base64.b64decode(data)
        elif src.startswith("blob:"):
            # Blob URL - need to fetch via browser
            return page.evaluate("""async (url) => {
                const response = await fetch(url);
                const blob = await response.blob();
                return await new Promise(resolve => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result.split(',')[1]);
                    reader.readAsDataURL(blob);
                });
            }""", src)
        else:
            # Regular HTTP URL
            return page.evaluate("""async (url) => {
                const response = await fetch(url);
                const blob = await response.blob();
                return await new Promise(resolve => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result.split(',')[1]);
                    reader.readAsDataURL(blob);
                });
            }""", src)
    except Exception:
        return None


def _extract_text_from_image(image_bytes: bytes, gemini_api_key: str = "", groq_api_key: str = "") -> str:
    """Extract text from image using AI vision (Gemini) with local fallback."""
    # Try AI vision first
    if gemini_api_key:
        try:
            from whatsapp_tracker.ai_extractor import extract_text_from_image as ai_extract
            text = ai_extract(image_bytes, gemini_api_key, groq_api_key)
            if text:
                return text
        except Exception:
            pass

    # Fallback: Local Tesseract
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert('L')
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception:
        return ""


def _open_group(page, group_name: str) -> bool:
    """Find a group by typing in the search box and clicking the result."""
    try:
        # Try multiple ways to find and click the search box
        search_clicked = False
        search_selectors = [
            '[data-testid="chat-list-search"]',
            'div[contenteditable="true"][data-tab="3"]',
            'div[aria-label="Search input textbox"]',
            'div[role="textbox"]',
            'div[title="Search input textbox"]',
            'span[data-icon="search"]',  # click search icon first
        ]
        for sel in search_selectors:
            try:
                elem = page.locator(sel).first
                if elem.is_visible(timeout=2000):
                    elem.click()
                    time.sleep(0.5)
                    search_clicked = True
                    break
            except Exception:
                continue

        if not search_clicked:
            # Last resort: use keyboard shortcut Ctrl+F to open search
            page.keyboard.press("Control+f")
            time.sleep(1)

        # Clear any existing text and type group name
        page.keyboard.press("Control+a")
        page.keyboard.press("Backspace")
        time.sleep(0.3)
        page.keyboard.type(group_name, delay=80)
        time.sleep(3)  # wait for search results

        # Try to find the chat result matching the group name
        # WhatsApp shows results as list items
        result_selectors = [
            f'span[title="{group_name}"]',
            f'div[title="{group_name}"]',
            '[data-testid="cell-frame-container"]',
            'div[role="listitem"]',
        ]
        for sel in result_selectors:
            try:
                items = page.locator(sel)
                count = items.count()
                if count > 0:
                    items.first.click()
                    time.sleep(2)
                    return True
            except Exception:
                continue

        return False

    except Exception as e:
        print(f"     search error: {e}")
        return False


def _read_messages(page, group_name: str, max_msgs: int, gemini_api_key: str = "", groq_api_key: str = "") -> list[dict]:
    messages = []
    seen_hashes = set()

    # 1. Read text messages
    for msg_sel in _MSG_TEXT:
        try:
            elems = page.locator(msg_sel).all()
            if not elems:
                continue
            for elem in elems[-max_msgs:]:
                try:
                    text = elem.inner_text().strip()
                    if len(text) < 80:
                        continue
                    h = hashlib.md5(f"{group_name}:{text[:200]}".encode()).hexdigest()
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        messages.append({
                            "group": group_name,
                            "text": text,
                            "hash": h,
                            "scraped_at": datetime.now().isoformat(),
                        })
                except Exception:
                    continue
            break
        except Exception:
            continue

    # 2. Read image messages (AI Vision OCR)
    for img_sel in _MSG_IMAGE:
        try:
            img_elems = page.locator(img_sel).all()
            if not img_elems:
                continue
            for img_elem in img_elems[-max_msgs:]:
                try:
                    img_bytes = _download_image(page, img_elem)
                    if not img_bytes:
                        continue
                    ocr_text = _extract_text_from_image(img_bytes, gemini_api_key, groq_api_key)
                    if len(ocr_text) < 80:
                        continue
                    h = hashlib.md5(f"{group_name}:img:{ocr_text[:200]}".encode()).hexdigest()
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        messages.append({
                            "group": group_name,
                            "text": f"[IMAGE OCR] {ocr_text}",
                            "hash": h,
                            "scraped_at": datetime.now().isoformat(),
                        })
                except Exception:
                    continue
            break
        except Exception:
            continue

    return messages


def scrape_groups(target_groups: list[str], max_msgs: int = 50, headless: bool = False,
                  gemini_api_key: str = "", groq_api_key: str = "") -> list[dict]:
    """Main scraping entry point."""
    if not os.path.exists(SESSION_DIR):
        raise FileNotFoundError("Run first_run.py first to save a WhatsApp session.")

    all_messages = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=headless,
            channel="chromium",
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            page.goto(WA_URL, timeout=30_000)
            loaded = _wait_any(page, _CHAT_LIST, 40_000)
            if not loaded:
                raise RuntimeError("WhatsApp Web did not load. Run first_run.py again.")

            print("  [WA] WhatsApp Web ready", flush=True)
            time.sleep(3)

            for group in target_groups:
                print(f"  [WA] Reading: {group}", flush=True)
                found = _open_group(page, group)
                if not found:
                    print(f"       -> Group not found, skipping", flush=True)
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                    continue

                msgs = _read_messages(page, group, max_msgs, gemini_api_key, groq_api_key)
                all_messages.extend(msgs)
                print(f"       -> {len(msgs)} messages", flush=True)

                page.keyboard.press("Escape")
                time.sleep(1)

        finally:
            ctx.close()

    return all_messages


def list_all_groups(max_items: int = 80) -> list[str]:
    """List all chats visible in the left panel."""
    names = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR, headless=False,
            channel="chromium",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(WA_URL, timeout=30_000)
        _wait_any(page, _CHAT_LIST, 30_000)
        time.sleep(2)

        for sel in ['[data-testid="cell-frame-title"]', 'span[title]', 'div[title]']:
            try:
                elems = page.locator(sel).all()
                for e in elems[:max_items]:
                    n = e.inner_text().strip()
                    if n and n not in names and len(n) > 1:
                        names.append(n)
                if names:
                    break
            except Exception:
                continue

        ctx.close()
    return names


def scrape_groups(target_groups: list[str], max_msgs: int = 50, headless: bool = False) -> list[dict]:
    """Main scraping entry point."""
    if not os.path.exists(SESSION_DIR):
        raise FileNotFoundError("Run first_run.py first to save a WhatsApp session.")

    all_messages = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=headless,
            channel="chromium",
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            page.goto(WA_URL, timeout=30_000)
            loaded = _wait_any(page, _CHAT_LIST, 40_000)
            if not loaded:
                raise RuntimeError("WhatsApp Web did not load. Run first_run.py again.")

            print("  [WA] WhatsApp Web ready", flush=True)
            time.sleep(3)

            for group in target_groups:
                print(f"  [WA] Reading: {group}", flush=True)
                found = _open_group(page, group)
                if not found:
                    print(f"       -> Group not found, skipping", flush=True)
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                    continue

                msgs = _read_messages(page, group, max_msgs)
                all_messages.extend(msgs)
                print(f"       -> {len(msgs)} messages", flush=True)

                page.keyboard.press("Escape")
                time.sleep(1)

        finally:
            ctx.close()

    return all_messages
