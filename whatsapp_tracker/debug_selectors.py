"""Debug script - checks what selectors work in an open WhatsApp group."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(__file__), "wa_session")
WA_URL = "https://web.whatsapp.com"
GROUP = "Fresher Hunt"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR, headless=False, channel="chromium"
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(WA_URL, timeout=30000)
    page.wait_for_selector("#pane-side", timeout=30000)
    time.sleep(3)

    # Try to open search
    for sel in ['[data-testid="chat-list-search"]', 'span[data-icon="search"]', 'div[role="textbox"]']:
        try:
            e = page.locator(sel).first
            if e.is_visible(timeout=2000):
                e.click()
                print(f"Clicked search via: {sel}", flush=True)
                break
        except Exception:
            pass

    time.sleep(0.5)
    page.keyboard.type(GROUP, delay=80)
    time.sleep(3)

    # Click first result
    try:
        page.locator('[data-testid="cell-frame-container"]').first.click()
        print("Clicked first result", flush=True)
    except Exception as e:
        print(f"Could not click result: {e}", flush=True)

    time.sleep(3)

    # Test message selectors
    print("\n--- Message selector counts ---", flush=True)
    for sel in [
        '[data-testid="msg-text"]',
        ".selectable-text",
        "span.selectable-text",
        "div.copyable-text span",
        '[data-testid="conversation-panel-messages"]',
        "div[class*='message']",
        "div[data-id]",
    ]:
        try:
            count = page.locator(sel).count()
            print(f"  {sel}: {count}", flush=True)
        except Exception as e:
            print(f"  {sel}: ERROR {e}", flush=True)

    input("Press Enter to close browser...")
    ctx.close()
