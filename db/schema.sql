DROP TABLE IF EXISTS picks;
DROP TABLE IF EXISTS activity_log;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE DATABASE IF NOT EXISTS walmart_meats DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE walmart_meats;

-- 1. Users Table (Pre-configured for future auth expansion)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NULL, -- Nullable while skipping auth
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Products Table (Cleaned, streamlined, and decoupled from raw retail codes)
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    upc VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NULL,
    description TEXT NULL,
    food_condition VARCHAR(50) NULL,
    image_url VARCHAR(500) NULL,
    url VARCHAR(500) NOT NULL, -- Guaranteed destination for external links
    category VARCHAR(100) NOT NULL DEFAULT 'Other', -- Fallback for matching misses
    subcategory VARCHAR(255) NOT NULL DEFAULT 'Other', -- Fallback tag

    -- Operational Strategy Flags
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE,
    is_stocked BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY idx_products_sku (sku),
    UNIQUE KEY idx_products_upc (upc),
    INDEX idx_ui_filter (category, is_discontinued)

);

-- 3. Picks Table (The live, active To-Do Queue)
CREATE TABLE IF NOT EXISTS picks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL DEFAULT 1,
    quantity INT NOT NULL DEFAULT 1, -- Target case count for this active run
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY idx_user_product (user_id, product_id)
);

-- 4. Activity Log Table (Unified Floor Timeline)
CREATE TABLE IF NOT EXISTS activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL DEFAULT 1,
    product_id INT NULL, -- Nullable for floor cleans, temp checks, and generic notes
    action ENUM(
        'throw', 'cvp', 'vizpik', 'restock',
        'clean_daily', 'clean_pm', 'temp_check',
        'general_note', 'product_note', 'donate', 'floor_sweep', 'recovery'
    ) NOT NULL,

    -- Explicitly splitting cases vs retail units
    cases_qty INT NULL,  -- Populated for restock, vizpik, etc.
    units_qty INT NULL,  -- Populated for throws, donations, cpv, etc.

    notes TEXT NULL,     -- Context for actions or direct supervisor logs
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
