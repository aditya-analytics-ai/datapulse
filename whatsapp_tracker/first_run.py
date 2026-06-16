"""
first_run.py - Run this ONCE to link your WhatsApp account.
Opens a real browser window, scan QR with your phone, session saved.
After this, everything runs headless in background.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
import os, time

SESSION_DIR = os.path.join(os.path.dirname(__file__), "wa_session")

def save_session():
    os.makedirs(SESSION_DIR, exist_ok=True)
    print("=" * 50)
    print("  DataPulse - WhatsApp Session Setup")
    print("=" * 50)
    print("\n[*] A browser window will open.")
    print("    Scan the QR code with your WhatsApp app.")
    print("    (WhatsApp > Linked Devices > Link a Device)\n")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            args=["--start-maximized"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://web.whatsapp.com")

        print("[*] Waiting for QR scan (up to 2 minutes)...")
        logged_in = False
        for sel in ['[data-testid="chat-list"]', '#pane-side', '[aria-label="Chat list"]']:
            try:
                page.wait_for_selector(sel, timeout=120_000)
                logged_in = True
                break
            except Exception:
                continue

        if logged_in:
            print("\n[OK] Success! WhatsApp session saved.")
            print(f"[OK] Session stored at: {SESSION_DIR}")
            print("\nNext steps:")
            print("  python whatsapp_tracker/list_groups.py   <- see your groups")
            print("  python whatsapp_tracker/scheduler.py     <- start tracking")
        else:
            print("\n[!] Timed out. Please run this script again and scan faster.")

        time.sleep(3)
        ctx.close()

if __name__ == "__main__":
    save_session()
