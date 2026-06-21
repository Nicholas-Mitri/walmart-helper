import pyautogui
import time
import subprocess
import json
from bs4 import BeautifulSoup


def send_hotkey(key, modifier="command down"):
    script = f"""
    tell application "System Events"
        keystroke "{key}" using {{{modifier}}}
    end tell
    """
    subprocess.run(["osascript", "-e", script])


def fetch(url):
    subprocess.run(
        ["bash", "-c", f"printf %s {json.dumps("view-source:"+url)} | pbcopy"]
    )
    time.sleep(1)

    # Open the URL in your default browser
    subprocess.run(["osascript", "-e", 'tell application "Arc" to activate'])
    time.sleep(0.3)
    send_hotkey("esc", modifier="")
    send_hotkey("t")
    time.sleep(0.3)
    send_hotkey("v")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(2)
    send_hotkey("a")
    send_hotkey("c")
    send_hotkey("w")
    time.sleep(0.05)

    html = subprocess.run(["pbpaste"], capture_output=True, text=True).stdout

    soup = BeautifulSoup(html, "html.parser")

    # Find the product schema specifically (not the breadcrumb JSON-LD)
    script = soup.find(
        "script", {"type": "application/ld+json", "data-seo-id": "schema-org-product"}
    )
    data = json.loads(script.string)

    if isinstance(data, dict):
        # Single product page (like this ground beef example)
        name = data["name"]
        upc = data["gtin13"]
        sku = data["sku"]

    elif isinstance(data, list):
        # Multi-variant page (like the Wrangler pants example)
        name = data[0]["hasVariant"][0]["name"]
        # Find the variant that matches the SKU in the URL
        upc = data[0]["hasVariant"][0]["gtin13"]
        sku = data[0]["hasVariant"][0]["sku"]

    return name, upc, sku
