from math import ceil
import pyautogui
import time
import subprocess
import json, random
from bs4 import BeautifulSoup


# Function to send a hotkey combination using AppleScript and subprocess
def send_hotkey(key, modifier="command down"):
    """
    Sends the specified hotkey using AppleScript via subprocess.
    Args:
        key (str): The key to be pressed.
        modifier (str): The key modifier (default is command down).
    """
    script = f"""
    tell application "System Events"
        keystroke "{key}" using {{{modifier}}}
    end tell
    """
    subprocess.run(["osascript", "-e", script])


# Function to fetch the HTML source of a given URL by simulating GUI keypresses and clipboard copying
def fetch_html(url):
    """
    Opens a new tab, pastes the URL prepended with 'view-source:',
    copies all page content, closes the tab, and returns the HTML from the clipboard.
    Args:
        url (str): The URL of the product to fetch HTML for.
    Returns:
        str: The raw HTML content of the page.
    """
    subprocess.run(
        ["bash", "-c", f"printf %s {json.dumps('view-source:'+url)} | pbcopy"]
    )
    time.sleep(1)

    # send_hotkey("esc", modifier="")
    send_hotkey("t")  # Open new tab
    time.sleep(0.3)
    send_hotkey("v")  # Paste URL
    time.sleep(0.3)
    pyautogui.press("enter")  # Go to URL
    time.sleep(2)
    send_hotkey("a")  # Select all
    send_hotkey("c")  # Copy
    send_hotkey("w")  # Close tab
    time.sleep(0.05)

    return subprocess.run(["pbpaste"], capture_output=True, text=True).stdout


# Function to extract product info in dictionary format from a Walmart view-source HTML string
def extract_product_info(html: str) -> dict:
    """
    Parses the given HTML content using BeautifulSoup, searches for structured JSON-LD blocks,
    extracts and returns relevant product metadata.
    Args:
        html (str): The HTML string of the product page.
    Returns:
        dict: Dictionary containing extracted product information.
    """
    soup = BeautifulSoup(html, "html.parser")

    # --- JSON-LD blocks ---
    ld_scripts = soup.find_all("script", type="application/ld+json")
    product_data = {}
    breadcrumb_data = {}

    for script in ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]
        except (json.JSONDecodeError, TypeError):
            continue

        if data.get("@type") == "Product":
            product_data = data
        if data.get("@type") == "ProductGroup":  # product with variants
            product_data = data["hasVariant"][0]
        elif data.get("@type") == "BreadcrumbList":
            breadcrumb_data = data

    if not product_data:
        return {}

    # --- Breadcrumb path ---
    breadcrumb = [
        item["item"]["name"]
        for item in breadcrumb_data.get("itemListElement", [])
        if "item" in item
    ]
    # --- Offer ---
    offers = product_data.get("offers", [{}])
    offer = offers[0] if isinstance(offers, list) else offers

    # --- Additional properties ---
    extra = {p["name"]: p["value"] for p in product_data.get("additionalProperty", [])}

    return {
        "name": product_data.get("name"),
        "brand": product_data.get("brand", {}).get("name"),
        "sku": product_data.get("sku"),
        "UPC": product_data.get("gtin13"),
        "description": product_data.get("description"),
        "model": product_data.get("model"),
        "image_url": product_data.get("image"),
        # "price": offer.get("price"),
        # "currency": offer.get("priceCurrency"),
        # "availability": offer.get("availability"),
        # "condition": offer.get("itemCondition"),
        "url": offer.get("url"),
        # "delivery_method": offer.get("availableDeliveryMethod"),
        # "avg_rating": agg.get("ratingValue"),
        # "review_count": agg.get("reviewCount"),
        # "best_rating": agg.get("bestRating"),
        "breadcrumb": breadcrumb,
        "food_condition": extra.get("Food Condition"),
        # "reviews": reviews,
    }


# Function to populate or update the Walmart meats database JSON file using scraped URLs
def populate_walmart_db(batch_size=5, url_file="unprocessed_scraped_urls.txt"):
    """
    Reads the list of scraped URLs and the current local JSON database.
    Randomizes the URLs, then for each URL not already in the DB,
    fetches and extracts product data, and appends it to the DB file.
    Args:
        batch_size (int): The number of records to add in this run.
    """
    try:
        with open("walmart_meats_db.json", "r") as f:
            walmart_meats_db = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        walmart_meats_db = []

    # Get URLs from file and randomize the order
    with open(url_file, "r") as f:
        scraped_urls = [url.strip() for url in f.readlines()]
    random.shuffle(scraped_urls)

    print(f"Number of URLs to scrape: {len(scraped_urls)}")
    n_records = len(walmart_meats_db)
    print(f"Walmart meats DB currently has {n_records} products.")

    print(f"Number of records remaining to populate: {328-n_records}")
    print(f"Attempting to add {batch_size} records...")

    subprocess.run(["osascript", "-e", 'tell application "Arc" to activate'])

    for url in scraped_urls[:batch_size]:
        sku = url.split("/")[-1]
        # Search walmart_meats_db for an existing entry with the same SKU
        existing = next(
            (item for item in walmart_meats_db if item.get("sku") == sku), None
        )
        if existing:
            print(f"SKU {sku} already exists in DB, skipping URL: {url}")
            continue

        product_html = fetch_html(url)
        product_info = extract_product_info(product_html)
        if not product_info.get("UPC"):
            print(f"Scraping failed, skipping URL: {url}")
            continue
        walmart_meats_db.append(product_info)
        print(f"Added SKU {sku} to DB.")
        time.sleep(5)

    print(f"Number of records added in this run: {len(walmart_meats_db) - n_records}")

    with open("walmart_meats_db.json", "w") as f:
        json.dump(walmart_meats_db, f, indent=2)


def filter_unprocessed_urls():
    with open("walmart_meats_db.json", "r") as f:
        walmart_meats_db = json.load(f)
    with open("scraped_urls.txt", "r") as f:
        detected_urls = f.readlines()
    processed_count = 0
    unprocess_urls = []
    for url in detected_urls:
        processed = False
        sku = url.strip().split("/")[-1]

        for item in walmart_meats_db:
            if item.get("sku") == sku:
                processed = True
                processed_count += 1
                break
        if not processed:
            print("sku", sku)
            unprocess_urls.append(url.strip())

    with open("unprocessed_scraped_urls.txt", "w") as f:
        f.write("\n".join(unprocess_urls))

    print(f"Walmart meats DB currently has {len(walmart_meats_db)} products.")
    print(f"Number of detected_urls: {len(detected_urls)}")
    print(f"Number of processed: {processed_count}")
    print(f"Number of unprocessed: {len(unprocess_urls)}")


if __name__ == "__main__":

    filter_unprocessed_urls()
    for _ in range(1):
        populate_walmart_db(batch_size=10)
        time.sleep(30)
