# Walmart Meat Department Assistant

A FastAPI web application designed to accelerate onboarding and streamline daily operations for new Walmart associates in the meat department. This tool addresses critical pain points that emerge during the first weeks and months of employment, turning complex floor procedures into intuitive, guided workflows.

## 🎯 The Problem

Onboarding in a Walmart meat department is challenging:

- **Product Knowledge**: New associates struggle to memorize hundreds of product SKUs, UPCs, and locations
- **Task Coordination**: Managing multiple concurrent tasks (picks, restocks, throws, cleaning) without clear prioritization
- **Compliance & Accuracy**: Activity logging is tedious, error-prone, and disconnected from actual work
- **Speed**: Veterans work 3x faster than newcomers, but there's no structured way to accelerate that learning curve
- **Information Silos**: Product details (availability, URLs, categories) are scattered across multiple systems

New hires often feel overwhelmed, make mistakes, and take weeks to reach baseline productivity. This tool closes that gap.

## ✨ What It Does

### For New Associates

- **Instant Product Lookup** — Scan a barcode or search by name to instantly see product details, Walmart links, and images
- **Guided Task Management** — Visual pick lists replace overwhelming floor instructions; tap to mark tasks complete
- **Learning by Doing** — Every scanned product, every completed action reinforces memory through repetition
- **Real-Time Activity Log** — No post-shift paperwork; log actions as they happen with a single tap
- **Faster Confidence** — Go from confusion to competence in days, not weeks

### For Managers

- **Compliance & Visibility** — Every floor action is timestamped and traceable
- **Performance Data** — Activity logs reveal who's moving fast, where training gaps are, and what's causing slowdowns
- **Reduced Errors** — Structured workflows prevent common mistakes (wrong products, skipped steps)
- **Lower Turnover** — Better onboarding → faster ramp-up → higher job satisfaction

## 📸 Screenshots

### Catalog View
Browse products by category or search by name, SKU, UPC, or WIN. Tap the bookmark icon to add items to your pick list, or tap the external link to view the product on Walmart's website.

![Catalog](docs/screenshots/1-Catalog.PNG)

### Pick List View
Manage your active tasks in one place. Adjust quantities, mark items complete, or remove them from your list.

![Pick List](docs/screenshots/3-Pick%20List.PNG)

### Activity Log
Record floor actions as they happen — no end-of-shift paperwork. Select an action type (throw, restock, clean, temperature check, etc.), adjust quantities, and add notes if needed.

![Activity Log](docs/screenshots/4-Activity%20Log.PNG)

### Interactive Features
Long-press on catalog items to trigger an action sheet for quick operations, and tap the activity log button to instantly log actions with optional details.

![Action Sheet](docs/screenshots/2-Long%20Press%20in%20Catalog%20Action%20Sheet.PNG) ![Log Action](docs/screenshots/5-Activity%20Log%20Task%20Add%20Action%20Sheet.PNG)

## 🚀 Key Features

### Three-Tab UI

1. **Catalog** — Browse all products by category, search by name/SKU/UPC/WIN, tap to bookmark and create pick tasks
2. **Picks** — Live to-do list for products to pull; adjust quantities, mark complete, or remove items
3. **Activity Log** — Record floor actions (throws, restocks, cleaning, temperature checks, donations, etc.) with optional quantities and notes

### Barcode Scanner Support

- Scan UPC, SKU, or Walmart Item Number (WIN) directly from physical products or labels
- Intelligent routing: scanner automatically identifies product type and retrieves details
- Supports multiple barcode reader formats and normalizes codes for consistency
- Perfect for rapid lookups without typing

### Product Management

- Comprehensive product database with Walmart metadata (SKU, UPC, WIN, brand, category, images, links)
- Dynamic filtering by category and subcategory
- Direct links to Walmart product pages for detailed specs
- Track stock status and discontinued items

### Activity Logging

Valid actions include:
- `throw` — discard/waste
- `cvp` — customer value pricing
- `vizpik` — visual pick restock
- `restock` — restocking shelves
- `clean_daily` — routine cleaning
- `clean_pm` — end-of-shift deep clean
- `temp_check` — temperature monitoring (compliance)
- `general_note` — floor notes
- `product_note` — product-specific comments
- `donate` — charitable donation
- `floor_sweep` — maintenance
- `recovery` — customer service recovery

## 🛠️ Getting Started

### Prerequisites

- Python 3.9+
- MySQL 8.0+ (or SQLite for development)
- UV or pip

### Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd "Walmart Helper"
   ```

2. Create a `.env` file with database credentials:
   ```
   DB_PASSWORD=your_mysql_password
   MYSQL_DATABASE_URL=mysql+pymysql://user:password@localhost/walmart_meats
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   mysql -u root -p < db/schema.sql
   mysql -u root -p < db/seed.sql
   python db/populate_products.py
   ```

5. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

   The app will be available at `http://localhost:8000`

### Database Setup

The database schema is defined in [db/schema.sql](db/schema.sql). Product data is automatically populated from `data/walmart_meats_clean_final.json` via [db/populate_products.py](db/populate_products.py).

To reinitialize from scratch:
```sql
source db/schema.sql;
source db/seed.sql;
```

Then run the population script.

## 📱 Usage

### For Associates

1. **Open the app** in a web browser or mobile device on your phone/tablet
2. **Catalog Tab** — Find products by browsing categories or searching by name
3. **Add to Picks** — Tap the bookmark icon to add a product to your to-do list
4. **Scanner** — Use a barcode reader to instantly look up products
5. **Picks Tab** — Adjust quantities and mark tasks complete
6. **Activity Log Tab** — Record what you did (throw, restock, clean, etc.) with quantities and notes

### For Managers

- Monitor activity logs to track associate performance and identify training needs
- Use product lookup to answer customer questions faster
- Verify compliance (temperature checks, cleaning schedules) via timestamped logs

## 🏗️ Architecture

**Backend:** FastAPI with SQLAlchemy ORM and MySQL  
**Frontend:** Jinja2 templates with vanilla JavaScript (no build step)  
**Database:** Four core tables (Users, Products, Picks, ActivityLog)  

### Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Serve main UI |
| `GET` | `/products/` | List all products |
| `GET` | `/products/search` | Search products with filters |
| `GET` | `/picks_list/` | Get all picks |
| `POST` | `/picks_list/mark-for-pick` | Add a product to picks |
| `DELETE` | `/picks_list/unmark_for_pick/{id}` | Remove from picks |
| `PUT` | `/picks_list/update_quantity/{id}` | Update pick quantity |
| `GET` | `/activity_log/` | Get all activity records |
| `POST` | `/activity_log/log-activity` | Log a new activity |

See [CLAUDE.md](CLAUDE.md) for full router documentation.

## 📊 Data Model

### Product
- SKU, UPC, WIN (Walmart Item Number) — multiple ways to identify a product
- Name, brand, description
- Category and subcategory
- Image URL and Walmart product link
- Stock status and discontinued flag

### Pick
- Links a product to a user
- Includes quantity to pick
- Lightweight to-do item

### ActivityLog
- Records floor actions (throw, restock, clean, etc.)
- Timestamps automatically on server
- Optional: product reference, quantities (cases/units), notes
- Append-only audit trail

### User
- Simple staff member model with username and password hash

## 🔄 Workflow Example: New Associate's First Shift

1. **Manager shows app** — "Use this to find products and log your work"
2. **Associate scans a barcode** — App shows product name, image, category, Walmart link
3. **Associate creates a pick task** — Taps bookmark to add to to-do list
4. **Associate works through picks** — Removes items as completed
5. **Manager asks: "Did you check temps?"** — Associate opens Activity Log, taps "temp_check", enters notes
6. **End of shift** — All work is logged automatically; no manual timesheets or notebooks

**Result:** Faster onboarding, fewer mistakes, better morale.

## 🚧 Development

### Project Structure
```
├── main.py                 # Entry point, router registration
├── models.py               # SQLAlchemy ORM models
├── database.py             # Database connection & session factory
├── routers/
│   ├── pages.py            # Jinja2 template rendering
│   ├── product_catalog.py  # Product search & listing
│   ├── pick_list.py        # Pick CRUD operations
│   ├── activity_log.py     # Activity logging
│   └── api.py              # Placeholder for future APIs
├── db/
│   ├── schema.sql          # Database schema
│   ├── seed.sql            # Initial data
│   └── populate_products.py # Load products from JSON
├── templates/
│   ├── base.html           # Base layout
│   └── index.html          # Main UI
├── static/
│   └── app.js              # Client-side interactivity
└── data/
    └── walmart_meats_clean_final.json  # Product database
```

### Running Tests

```bash
pytest
```

### Code Style

Follow PEP 8. Use type hints where practical.

## 🎓 Pain Points Addressed

| Pain Point | How This Tool Helps |
|------------|-------------------|
| **Memorizing 500+ SKUs** | Search, browse, and barcode scanning reduce reliance on memory |
| **Scattered task info** | All tasks in one place (Pick list) |
| **Manual activity logging** | One-tap logging; no post-shift paperwork |
| **Slow product lookups** | Instant barcode scans and search |
| **Compliance gaps** | Timestamped audit trail for temperature checks, cleaning |
| **Onboarding overload** | Guided workflows feel more intuitive than floor instructions |
| **High turnover** | Faster competence = higher job satisfaction |
| **Manager visibility** | Real-time activity logs for performance tracking |

## 📝 Notes for Contributors

- The `get_db()` dependency is duplicated across routers (minor inconsistency; refactor if consolidating routers)
- Product data is versioned in JSON; updates require re-running `populate_products.py`
- UI is deliberately simple (no heavy frameworks) for fast load times on mobile devices
- Scanner logic normalizes UPC formats intelligently; see [static/app.js](static/app.js) for details

## 📄 License

(Add your license here)

## 👥 Contributing

Contributions are welcome! Please submit a pull request or open an issue for bugs and feature requests.

---

**Built with ❤️ to make the first few months at Walmart feel less overwhelming.**
