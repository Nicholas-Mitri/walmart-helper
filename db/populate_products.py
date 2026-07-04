import json
import os
import mysql.connector as mysql
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CLEAN_JSON_PATH = os.path.join("data", "walmart_meats_clean_final_w_WIN.json")

# Database Configuration
# Swap these placeholders out with your local environment credentials
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.environ.get("DB_PASSWORD_CONNECTOR", "your_password"),
    "database": "walmart_meats",
}
print(DB_CONFIG)


def seed_products_table():
    if not os.path.exists(CLEAN_JSON_PATH):
        print(f"Error: Missing cleaned dataset at {CLEAN_JSON_PATH}")
        return

    # 1. Load the processed JSON records
    with open(CLEAN_JSON_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} products from JSON. Initiating database insert...")

    connection = mysql.connect(**DB_CONFIG)
    try:
        # 2. Establish connection to local MySQL instance
        connection = mysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 3. Formulate the bulk insertion query
        # Using ON DUPLICATE KEY UPDATE keeps the script safe to run multiple times
        insert_query = """
            INSERT INTO products (
                sku, upc, name, brand, description,
                image_url, url, food_condition, category, subcategory, win
            ) VALUES (
                %(sku)s, %(upc)s, %(name)s, %(brand)s, %(description)s,
                %(image_url)s, %(url)s, %(food_condition)s, %(category)s, %(subcategory)s, %(win)s
            )
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                brand = VALUES(brand),
                upc = VALUES(upc),
                description = VALUES(description),
                image_url = VALUES(image_url),
                url = VALUES(url),
                food_condition = VALUES(food_condition),
                category = VALUES(category),
                subcategory = VALUES(subcategory),
                win = VALUES(win)
        """

        # 4. Execute bulk operation safely inside a transaction
        cursor.executemany(insert_query, products)
        connection.commit()

        print(
            f"Success! Safely populated 'products' table with {cursor.rowcount} records."
        )

    except Error as e:
        print(f"Database Error: {e}")
        if connection:
            connection.rollback()
            print("Transaction rolled back successfully.")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")


if __name__ == "__main__":
    seed_products_table()
