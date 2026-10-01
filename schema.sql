-- =======================================================
-- JerseyHub - Football Jersey E-Commerce Database Schema
-- College DBMS Mini / Major Project
-- Target RDBMS: MySQL 8.0+ / MariaDB 10.4+
-- =======================================================

CREATE DATABASE IF NOT EXISTS `jerseyhub_db`
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `jerseyhub_db`;

-- 1. USERS TABLE
DROP TABLE IF EXISTS `contact_messages`;
DROP TABLE IF EXISTS `reviews`;
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `cart_items`;
DROP TABLE IF EXISTS `product_variants`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `teams`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(80) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(120) NULL,
    `phone` VARCHAR(25) NULL,
    `address` TEXT NULL,
    `city` VARCHAR(80) NULL,
    `state` VARCHAR(80) NULL,
    `postal_code` VARCHAR(20) NULL,
    `country` VARCHAR(80) DEFAULT 'India',
    `is_admin` BOOLEAN NOT NULL DEFAULT FALSE,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. CATEGORIES (Leagues / Kit Categories)
CREATE TABLE `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `slug` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `image_url` VARCHAR(500) NULL,
    `display_order` INT DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_categories_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. TEAMS TABLE
CREATE TABLE `teams` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `slug` VARCHAR(100) NOT NULL,
    `category_id` INT NOT NULL,
    `logo_url` VARCHAR(500) NULL,
    `country` VARCHAR(100) NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_teams_slug` (`slug`),
    CONSTRAINT `fk_teams_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. PRODUCTS (Jerseys) TABLE
CREATE TABLE `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL,
    `slug` VARCHAR(160) NOT NULL UNIQUE,
    `team_id` INT NOT NULL,
    `category_id` INT NULL,
    `description` TEXT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `discount_price` DECIMAL(10, 2) NULL,
    `season` VARCHAR(20) DEFAULT '2024/25',
    `kit_type` VARCHAR(30) DEFAULT 'Home',
    `gender` VARCHAR(20) DEFAULT 'Men',
    `primary_image` VARCHAR(500) NOT NULL,
    `secondary_image` VARCHAR(500) NULL,
    `is_featured` BOOLEAN NOT NULL DEFAULT FALSE,
    `is_bestseller` BOOLEAN NOT NULL DEFAULT FALSE,
    `is_new_arrival` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_products_slug` (`slug`),
    INDEX `idx_products_featured` (`is_featured`),
    INDEX `idx_products_bestseller` (`is_bestseller`),
    INDEX `idx_products_new_arrival` (`is_new_arrival`),
    CONSTRAINT `fk_products_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. PRODUCT VARIANTS (Sizes & Inventory Management)
CREATE TABLE `product_variants` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `product_id` INT NOT NULL,
    `size` VARCHAR(10) NOT NULL,
    `stock_quantity` INT NOT NULL DEFAULT 0,
    `sku` VARCHAR(50) UNIQUE NULL,
    CONSTRAINT `fk_variants_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. CART ITEMS TABLE
CREATE TABLE `cart_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `variant_id` INT NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_cart_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cart_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cart_variant` FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. ORDERS TABLE
CREATE TABLE `orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_number` VARCHAR(30) NOT NULL UNIQUE,
    `user_id` INT NULL,
    `subtotal` DECIMAL(10, 2) NOT NULL,
    `shipping_fee` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `total_amount` DECIMAL(10, 2) NOT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'Pending',
    `shipping_name` VARCHAR(120) NOT NULL,
    `shipping_phone` VARCHAR(25) NOT NULL,
    `shipping_address` TEXT NOT NULL,
    `shipping_city` VARCHAR(80) NOT NULL,
    `shipping_state` VARCHAR(80) NULL,
    `shipping_postal_code` VARCHAR(20) NOT NULL,
    `shipping_country` VARCHAR(80) DEFAULT 'India',
    `notes` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_orders_user` (`user_id`),
    INDEX `idx_orders_status` (`status`),
    CONSTRAINT `fk_orders_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. ORDER ITEMS TABLE
CREATE TABLE `order_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `product_id` INT NULL,
    `variant_id` INT NULL,
    `product_name` VARCHAR(150) NOT NULL,
    `size` VARCHAR(10) NOT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `total_price` DECIMAL(10, 2) NOT NULL,
    CONSTRAINT `fk_orderitems_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_orderitems_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_orderitems_variant` FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. PAYMENTS TABLE
CREATE TABLE `payments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL UNIQUE,
    `transaction_id` VARCHAR(100) NOT NULL UNIQUE,
    `payment_method` VARCHAR(50) NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `payment_status` VARCHAR(30) NOT NULL DEFAULT 'Completed',
    `payment_details` TEXT NULL,
    `paid_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_payments_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. REVIEWS & RATINGS TABLE
CREATE TABLE `reviews` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `rating` INT NOT NULL CHECK (`rating` >= 1 AND `rating` <= 5),
    `comment` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_reviews_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_reviews_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. CONTACT MESSAGES TABLE
CREATE TABLE `contact_messages` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(120) NOT NULL,
    `subject` VARCHAR(150) NULL,
    `message` TEXT NOT NULL,
    `is_read` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =======================================================
-- DBMS VIEWS FOR REPORTING & ANALYTICS
-- =======================================================

-- View: Low Stock Alerts
CREATE OR REPLACE VIEW `view_low_stock` AS
SELECT 
    p.id AS product_id,
    p.name AS product_name,
    v.size,
    v.stock_quantity,
    t.name AS team_name,
    c.name AS category_name
FROM product_variants v
JOIN products p ON v.product_id = p.id
JOIN teams t ON p.team_id = t.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE v.stock_quantity <= 5;

-- View: Product Sales Performance
CREATE OR REPLACE VIEW `view_sales_summary` AS
SELECT 
    oi.product_name,
    SUM(oi.quantity) AS total_units_sold,
    SUM(oi.total_price) AS total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
WHERE o.status != 'Cancelled'
GROUP BY oi.product_name
ORDER BY total_revenue DESC;
