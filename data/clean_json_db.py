category_tags = {
    "beef": [
        "beef",
        "lamb",
        "AA",
        "AAA",
    ],
    "pork": ["pork", "ham", "chop"],
    "poultry": ["chicken", "turkey", "poultry", "wings"],
    "seafood": [
        "fish",
        "salmon",
        "basa",
        "seafood",
        "crab",
        "shrimp",
    ],
    "ready": [
        "ready-to-Eat",
        "pre-cooked",
        "cooked",
        "deli",
        "prepared",
        "salami",
        "pepperoni",
        "smoked",
        "smokies",
        "breast",
        "strips",
    ],
}
subcategory_tags = {
    "beef": [
        "lamb",
        "bacon",
        "frankfurters",
        "strips",
        "ground",
        "hot dog",
        "wiener",
        "sausage",
        "roast",
        "steak",
        "meatball",
        "loin",
        "sirloin",
        "striploin",
        "round",
        "AA",
        "AAA",
        "medallions",
        "tube",
        "sojuk",
        "cubes",
    ],
    "pork": [
        "loin",
        "sirloin",
        "ribend",
        "chops",
        "bacon",
        "frankfurters",
        "ground",
        "hot dog",
        "wiener",
        "sausage",
        "meatball",
        "rib",
        "ham",
        "tube",
        "tenderloin",
        "belly",
        "shoulder",
        "kabob",
        "kebab",
        "ribette",
    ],
    "poultry": [
        "marinated",
        "bacon",
        "frankfurters",
        "ground",
        "sausage",
        "wiener",
        "leg",
        "breast",
        "wing",
        "drumstick",
        "thigh",
        "souvlaki",
        "kebab",
        "skewer",
        "drummettes",
        "winglets",
        "whole",
        "kabob",
    ],
    "seafood": [
        "tilapia",
        "trout",
        "salmon",
        "coho",
        "basa",
        "atlantic",
        "crab",
        "shrimp",
    ],
    "ready": [
        "sausage",
        "bacon",
        "wiener",
        "frankfurter",
        "ribs",
        "meatball",
        "salami",
        "pepperoni",
    ],
}

brands = [
    "Alpha Foods",
    "Hormel",
    "Paramount",
    "Piller's",
    "Mina",
    "Greenfield",
    "Deli Express",
    "Our Finest",
    "SOLMAZ",
    "Grimm's",
    "Springvale",
    "Aquamar Classic",
    "Maple Lodge Farms",
    "Swiss Chalet",
    "Fontaine Santé",
    "Zabiha Halal",
    "Marcangelo",
    "Barakah Meadows",
    "Kam Yen Jan",
    "Your Fresh Market",
    "Butterball",
    "Butchers Selection",
    "Great Value",
    "Siwin",
    "Our Promise",
    "Kebab Factory",
    "Schneider's",
    "Sunrise Soya Foods",
    "Lightlife",
    "Black River",
    "Master Wang",
    "Schneiders",
    "Johnsonville",
    "High Liner",
    "Maple Leaf",
    "Chata",
    "Harvest Meats",
    "Prime",
    "Dalisa",
    "Fletchers",
]

import json
import os, re

# Define file paths
RAW_JSON_PATH = os.path.join("data", "walmart_meats_db_pruned.json")
CLEAN_JSON_PATH = os.path.join("data", "walmart_meats_clean.json")


def clean_brand(brand_raw):
    if not brand_raw:
        return "Other"  # Fallback for Walmart's private label if blank

    brand = str(brand_raw).strip().lower()
    # Normalize common brand variations
    if "schneider" in brand:
        return "Schneider's"
    return brand


def determine_floor_categories(item):
    name = item.get("name", "").lower()
    # Combine breadcrumbs into a single string for keyword hunting
    breadcrumbs = " ".join(item.get("breadcrumb", [])[-2:]).lower()
    description = item.get("description", "").lower()

    partial_text = f"{name} {breadcrumbs}"
    full_text = f"{name} {breadcrumbs} {description}"

    # 1. Determine Major Floor Category
    if any(k in partial_text for k in category_tags["ready"]):
        category = "Ready to eat"
        subcategory = ";".join(
            [
                sub
                for sub in subcategory_tags["ready"]
                if re.search(r"\b" + re.escape(sub) + r"s?\b", partial_text)
            ]
        )
    elif any(k in full_text for k in category_tags["beef"]):
        category = "Raw Beef"
        subcategory = ";".join(
            [
                sub
                for sub in subcategory_tags["beef"]
                if re.search(r"\b" + re.escape(sub) + r"s?\b", partial_text)
            ]
        )
    elif any(k in full_text for k in category_tags["pork"]):
        category = "Raw Pork"
        subcategory = ";".join(
            [
                sub
                for sub in subcategory_tags["pork"]
                if re.search(r"\b" + re.escape(sub) + r"s?\b", partial_text)
            ]
        )
    elif any(k in full_text for k in category_tags["poultry"]):
        category = "Raw Poultry"
        subcategory = ";".join(
            [
                sub
                for sub in subcategory_tags["poultry"]
                if re.search(r"\b" + re.escape(sub) + r"s?\b", partial_text)
            ]
        )
    elif any(k in full_text for k in category_tags["seafood"]):
        category = "Raw Fish"
        subcategory = ";".join(
            [
                sub
                for sub in subcategory_tags["seafood"]
                if re.search(r"\b" + re.escape(sub) + r"s?\b", partial_text)
            ]
        )
    else:
        category = "Other"
        subcategory = "Other"

    return category, subcategory


def process_database():
    if not os.path.exists(RAW_JSON_PATH):
        print(f"Error: Could not find raw file at {RAW_JSON_PATH}")
        return

    with open(RAW_JSON_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    cleaned_items = []

    for item in items:
        # Extract and map fields
        category, subcategory = determine_floor_categories(item)

        clean_item = {
            "sku": str(item.get("sku", "")).strip(),
            "upc": str(item.get("UPC", "")).strip(),
            "name": item.get("name", "").strip(),
            "brand": clean_brand(item.get("brand")),
            "description": item.get("description", ""),
            "image_url": item.get("image_url", ""),
            "url": item.get("url", ""),
            "food_condition": item.get("food_condition", "Raw"),
            "category": category,
            "subcategory": subcategory,
        }

        # Keep data hygiene high: skip missing essential keys
        if clean_item["sku"] and clean_item["upc"]:
            cleaned_items.append(clean_item)
        # cleaned_items.append(clean_item)

    with open(CLEAN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_items, f, indent=4, ensure_ascii=False)

    print(f"Success! Processed {len(cleaned_items)} items. Saved to {CLEAN_JSON_PATH}")


if __name__ == "__main__":
    process_database()
