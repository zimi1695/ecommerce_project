USE ecommerce;

-- ============================================================
-- 1. users
-- ============================================================

INSERT INTO users (user_id)
SELECT DISTINCT
    user_id
FROM staging_events;


-- ============================================================
-- 2. categories
-- category_id -> category_code is known to be stable
-- ============================================================

INSERT INTO categories (
    category_id,
    category_code
)
SELECT
    category_id,
    MAX(category_code) AS category_code
FROM staging_events
GROUP BY category_id;


-- ============================================================
-- 3. brands
-- Only non-null / non-empty brand names are loaded.
-- ============================================================

INSERT INTO brands (brand_name)
SELECT DISTINCT
    TRIM(brand)
FROM staging_events
WHERE brand IS NOT NULL
  AND TRIM(brand) <> '';


-- ============================================================
-- 4. products
-- product_id -> category_id is known to be stable
-- ============================================================

INSERT INTO products (
    product_id,
    category_id
)
SELECT
    product_id,
    MIN(category_id)
FROM staging_events
GROUP BY product_id;


-- ============================================================
-- 5. product_brands
-- Many-to-many relationship.
-- ============================================================

INSERT INTO product_brands (
    product_id,
    brand_id
)
SELECT DISTINCT
    s.product_id,
    b.brand_id
FROM staging_events s
JOIN brands b
  ON b.brand_name = TRIM(s.brand)
WHERE s.brand IS NOT NULL
  AND TRIM(s.brand) <> '';


-- ============================================================
-- 6. sessions
-- Session is not directly tied to one user.
-- ============================================================

INSERT INTO sessions (
    session_id,
    start_time,
    end_time,
    event_count
)
SELECT
    user_session AS session_id,

    MIN(
        STR_TO_DATE(
            REPLACE(event_time_raw, ' UTC', ''),
            '%Y-%m-%d %H:%i:%s'
        )
    ) AS start_time,

    MAX(
        STR_TO_DATE(
            REPLACE(event_time_raw, ' UTC', ''),
            '%Y-%m-%d %H:%i:%s'
        )
    ) AS end_time,

    COUNT(*) AS event_count

FROM staging_events

WHERE user_session IS NOT NULL

GROUP BY user_session;