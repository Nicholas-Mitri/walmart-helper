import pyautogui
import time
import subprocess
import json, random
from bs4 import BeautifulSoup
import re


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
    send_hotkey("l")  # Open new tab
    time.sleep(0.3)
    send_hotkey("v")  # Paste URL
    time.sleep(0.3)
    pyautogui.press("enter")  # Go to URL
    time.sleep(3)
    send_hotkey("a")  # Select all
    send_hotkey("c")  # Copy
    # send_hotkey("w")  # Close tab
    time.sleep(0.05)

    return subprocess.run(["pbpaste"], capture_output=True, text=True).stdout


def extract_product_sku(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    tile = soup.find("div", attrs={"data-dca-id": True})
    return tile["data-dca-id"]


def upc_to_url(start_index=0, n_scrapes=10):
    with open("./scraper/newly_scanned_upcs.txt", "r") as f:
        upc_list = [line.strip() for line in f.readlines()]

    if not upc_list:
        print("No newly scanned upcs to process. Exiting...")
        return

    newly_scanned_urls = []
    subprocess.run(["osascript", "-e", 'tell application "Arc" to activate'])

    try:
        for i in range(start_index, start_index + n_scrapes):
            upc = upc_list[i]
            url = f"https://www.walmart.ca/en/search?q={upc}"
            print(f"Retreiving url: {url}")
            html = fetch_html(url)
            sku = extract_product_sku(html)
            if sku:
                newly_scanned_urls.append(f"https://www.walmart.ca/ip/{sku}" + "\n")
            time.sleep(10)

        print(
            f"Scraping complete! Retrieved {n_scrapes} urls. Starting index can be incremented by {n_scrapes}."
        )

    except Exception as e:
        print(f"Something went wrong. Error: {e} \n Restart next scrape at {i}.")

    # Write the converted URLs into newly_scanned_urls.txt
    with open("./scraper/newly_scanned_urls.txt", "a") as f:
        f.writelines(newly_scanned_urls[: i - start_index])


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

    ## Extract WIN

    match = re.search(r'{"name":"Walmart Item #","value":"(\d+)"', html)
    win = None
    if match:
        win = str(match.group(1))

    return {
        "name": product_data.get("name"),
        "brand": product_data.get("brand", {}).get("name"),
        "sku": product_data.get("sku"),
        "upc": product_data.get("gtin13"),
        "description": product_data.get("description"),
        "model": product_data.get("model"),
        "image_url": product_data.get("image"),
        "win": win,
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


def add_newly_scanned_urls():
    """
    Adds any new URLs from 'newly_scanned_urls.txt' to 'scraped_urls.txt',
    but skips URLs that already exist in the scraped file.

    Reads each URL from 'newly_scanned_urls.txt'. If the URL is not already present
    in 'scraped_urls.txt', it is appended to that file to prevent duplicates.
    Prints out how many new URLs were added.

    This function does nothing if no new URLs are found or if the file is missing.
    """
    new_urls_path = "./scraper/newly_scanned_urls.txt"
    scraped_urls_path = "./scraper/scraped_urls.txt"

    # Read in all new URLs found by the latest scan
    try:
        with open(new_urls_path, "r") as f:
            new_urls = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print(f"No new urls found at {new_urls_path}.")
        return

    # Read the URLs that have already been scraped (if any)
    try:
        with open(scraped_urls_path, "r") as f:
            existing_urls = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        existing_urls = set()

    # Figure out which URLs are actually new
    urls_to_add = new_urls - existing_urls
    if not urls_to_add:
        print("No new URLs to add.")
        return

    # Add new URLs to the scraped URLs file
    with open(scraped_urls_path, "a") as f:
        for url in sorted(urls_to_add):
            f.write(url + "\n")

    print(f"Added {len(urls_to_add)} new URLs to {scraped_urls_path}.")


def filter_unprocessed_urls():
    """
    Writes all URLs from 'scraped_urls.txt' that have not yet been processed
    (i.e., whose SKU is not present in 'walmart_meats_db.json') to 'unprocessed_urls.txt'.
    Also prints stats: total DB products, detected URLs, processed and unprocessed counts.

    Reads:
        - 'walmart_meats_db.json': The local product DB.
        - 'scraped_urls.txt': URLs (one per line), typically from scanning or scraping.

    Writes:
        - 'unprocessed_urls.txt': Only the URLs whose SKU is not found in the DB.

    Effects:
        - Useful for batch-incremental scraping. Run before scrape jobs to refresh the scrape target list.
    """
    with open("./data/walmart_meats_db.json", "r") as f:
        walmart_meats_db = json.load(f)
    with open("./scraper/scraped_urls.txt", "r") as f:
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

    with open("./scraper/unprocessed_urls.txt", "w") as f:
        f.write("\n".join(unprocess_urls))

    print(f"Walmart meats DB currently has {len(walmart_meats_db)} products.")
    print(f"Number of detected_urls: {len(detected_urls)}")
    print(f"Number of processed: {processed_count}")
    print(f"Number of unprocessed: {len(unprocess_urls)}")


# Function to populate or update the Walmart meats database JSON file using scraped URLs
def populate_walmart_db(batch_size=5, url_file="./scraper/unprocessed_urls.txt"):
    """
    Reads the list of scraped URLs and the current local JSON database.
    Randomizes the URLs, then for each URL not already in the DB,
    fetches and extracts product data, and appends it to the DB file.
    Args:
        batch_size (int): The number of records to add in this run.
    """
    new_meats_records = []

    with open("./data/walmart_meats_db.json", "r") as f:
        walmart_meats_db = json.load(f)

    # Get URLs from file
    with open(url_file, "r") as f:
        unprocessed_urls = [url.strip() for url in f.readlines()]
        if not unprocessed_urls:
            print("No unprocessed URLs to add. Exiting.")
            return

        unprocessed_urls_updated = unprocessed_urls.copy()

    n_unprocessed = len(unprocessed_urls)
    print(f"Number of URLs to scrape: {n_unprocessed}")
    print(f"Attempting to add {batch_size} records...")

    subprocess.run(["osascript", "-e", 'tell application "Arc" to activate'])

    for url in unprocessed_urls[: min(n_unprocessed, batch_size)]:
        sku = url.split("/")[-1]
        product_html = fetch_html(url)
        product_info = extract_product_info(product_html)
        if not product_info.get("UPC"):
            print(f"Scraping failed, skipping URL: {url}")
            continue
        new_meats_records.append(product_info)
        unprocessed_urls_updated.remove(url)
        print(f"Added SKU {sku} to DB.")
        time.sleep(5)

    print(f"Number of records added in this run: {len(new_meats_records)}")

    walmart_meats_db.extend(new_meats_records)
    with open("./data/walmart_meats_db.json", "w") as f:
        json.dump(walmart_meats_db, f, indent=2)

    with open("./data/diff_walmart_meats_db.json", "w") as f:
        json.dump(new_meats_records, f, indent=2)

    # Overwrite url_file with the updated unprocessed URLs (those not just added)
    with open(url_file, "w") as f:
        for url in unprocessed_urls_updated:
            f.write(url + "\n")


def add_win_to_records(start_item_upc=None):
    with open("./data/walmart_meats_clean_final.json", "r") as f:
        products = json.load(f)
    print(f"Older version of DB has {len(products)} records")
    with open("./data/walmart_meats_clean_final_w_WIN.json", "r") as f:
        products_with_win = json.load(f)
    print(f"New version of DB has {len(products_with_win)} records")

    last_pulled_upc = "xxx"
    start_idx = (
        next((i + 1 for i, d in enumerate(products) if d["upc"] == start_item_upc))
        if start_item_upc
        else 0
    )
    subprocess.run(["osascript", "-e", 'tell application "Arc" to activate'])
    for item in products[start_idx:]:
        time.sleep(5)
        item_info = extract_product_info(fetch_html(item["url"]))
        win = item_info.get("win", None)
        if not win:
            print(
                f"Failed. Last extracted WIN is for record with upc: {last_pulled_upc}."
            )
            if products_with_win:
                with open("./data/walmart_meats_clean_final_w_WIN.json", "w") as fw:
                    json.dump(products_with_win, fw, indent=2)
            return
        else:
            new_item = dict(item)
            new_item["win"] = win
            last_pulled_upc = item_info["upc"]
            products_with_win.append(new_item)
            print(
                f"Success. Last extracted WIN is for record with upc: {last_pulled_upc} with win: {win}."
            )
            if products_with_win:
                with open("./data/walmart_meats_clean_final_w_WIN.json", "w") as fw:
                    json.dump(products_with_win, fw, indent=2)


if __name__ == "__main__":

    # upc_to_url(start_index=104, n_scrapes=7)
    # add_newly_scanned_urls()
    # filter_unprocessed_urls()
    # for _ in range(10):
    #     populate_walmart_db(batch_size=5)
    #     time.sleep(30)
    add_win_to_records(start_item_upc="773220108343")
