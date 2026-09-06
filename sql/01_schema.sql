-- ============================================================
-- E-commerce User Behavior Analysis System
-- Database Schema v1.0
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecommerce
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE ecommerce;

-- ------------------------------------------------------------
-- 1. users
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 2. categories
-- category_id -> category_code has been verified to be stable
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id BIGINT UNSIGNED NOT NULL,
    category_code VARCHAR(255) NULL,
    PRIMARY KEY (category_id)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 3. brands
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS brands (
    brand_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    brand_name VARCHAR(255) NOT NULL,
    PRIMARY KEY (brand_id),
    UNIQUE KEY uk_brand_name (brand_name)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 4. products
-- product_id -> category_id is stable
-- price is deliberately NOT stored here
-- brand is deliberately NOT stored here because 136 products
-- were observed with multiple non-null brand values.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT UNSIGNED NOT NULL,
    category_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (product_id),
    KEY idx_products_category (category_id)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 5. product_brands
-- Many-to-many relationship between products and brands.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_brands (
    product_id BIGINT UNSIGNED NOT NULL,
    brand_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (product_id, brand_id),

    KEY idx_product_brands_brand (brand_id)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 6. sessions
-- A session is intentionally NOT tied to a single user because
-- 591 session IDs were observed with multiple user IDs.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    session_id CHAR(36) NOT NULL,
    start_time DATETIME(3) NOT NULL,
    end_time DATETIME(3) NOT NULL,
    event_count INT UNSIGNED NOT NULL DEFAULT 0,

    PRIMARY KEY (session_id)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 7. behavior_events
-- Largest fact table.
-- Foreign keys are added later, after bulk loading.
-- This keeps the initial 67M-row import practical.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS behavior_events (
    event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    event_time DATETIME(3) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    session_id CHAR(36) NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    brand_id INT UNSIGNED NULL,
    price DECIMAL(10,2) NOT NULL,
    source_event_hash BINARY(32) NOT NULL,

    PRIMARY KEY (event_id),
    UNIQUE KEY uk_source_event_hash (source_event_hash)
) ENGINE=InnoDB;



-- ============================================================
-- ETL staging table
-- Raw event layer. This table is used during data loading and
-- transformation, and is not part of the final business model.
-- ============================================================

CREATE TABLE IF NOT EXISTS staging_events (
    staging_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    event_time_raw VARCHAR(32) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    category_id BIGINT UNSIGNED NOT NULL,
    category_code VARCHAR(255) NULL,
    brand VARCHAR(255) NULL,
    price DECIMAL(10,2) NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    user_session CHAR(36) NULL,

    PRIMARY KEY (staging_id)
) ENGINE=InnoDB;
