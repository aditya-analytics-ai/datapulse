"""
list_groups.py - Helper to list all your WhatsApp chats/groups.
Run this after first_run.py to find exact group names for config.py.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whatsapp_tracker.wa_scraper import list_all_groups

if __name__ == "__main__":
    print("[*] Fetching your WhatsApp chats...")
    print("    (A browser window will open briefly)\n")
    groups = list_all_groups(max_items=80)

    if not groups:
        print("[!] No groups found. Make sure you ran first_run.py first.")
    else:
        print(f"Found {len(groups)} chats/groups:\n")
        for i, name in enumerate(groups, 1):
            print(f"  {i:>3}. {name}")
        print("\nCopy the group names you want into config.py -> TARGET_GROUPS")
