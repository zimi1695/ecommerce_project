USE ecommerce;

-- ============================================================
-- Product statistics
-- ============================================================
CREATE OR REPLACE VIEW v_product_statistics AS
SELECT
    p.product_id,
    p.category_id,
    c.category_code,
    COUNT(e.event_id) AS event_count,
    COUNT(CASE WHEN e.event_type = 'view' THEN 1 END) AS view_count,
    COUNT(CASE WHEN e.event_type = 'cart' THEN 1 END) AS cart_count,
    COUNT(CASE WHEN e.event_type = 'purchase' THEN 1 END) AS purchase_count,
    COALESCE(
        SUM(
            CASE
                WHEN e.event_type = 'purchase'
                THEN e.price
                ELSE 0
            END
        ),
        0
    ) AS sales_amount
FROM products p
LEFT JOIN categories c
    ON c.category_id = p.category_id
LEFT JOIN behavior_events e
    ON e.product_id = p.product_id
GROUP BY
    p.product_id,
    p.category_id,
    c.category_code;


-- ============================================================
-- Brand statistics
-- ============================================================
CREATE OR REPLACE VIEW v_brand_statistics AS
SELECT
    b.brand_id,
    b.brand_name,
    COUNT(e.event_id) AS event_count,
    COUNT(CASE WHEN e.event_type = 'view' THEN 1 END) AS view_count,
    COUNT(CASE WHEN e.event_type = 'cart' THEN 1 END) AS cart_count,
    COUNT(CASE WHEN e.event_type = 'purchase' THEN 1 END) AS purchase_count,
    COALESCE(
        SUM(
            CASE
                WHEN e.event_type = 'purchase'
                THEN e.price
                ELSE 0
            END
        ),
        0
    ) AS sales_amount
FROM brands b
LEFT JOIN behavior_events e
    ON e.brand_id = b.brand_id
GROUP BY
    b.brand_id,
    b.brand_name;


-- ============================================================
-- Category statistics
-- ============================================================
CREATE OR REPLACE VIEW v_category_statistics AS
SELECT
    c.category_id,
    c.category_code,
    COUNT(e.event_id) AS event_count,
    COUNT(CASE WHEN e.event_type = 'view' THEN 1 END) AS view_count,
    COUNT(CASE WHEN e.event_type = 'cart' THEN 1 END) AS cart_count,
    COUNT(CASE WHEN e.event_type = 'purchase' THEN 1 END) AS purchase_count,
    COALESCE(
        SUM(
            CASE
                WHEN e.event_type = 'purchase'
                THEN e.price
                ELSE 0
            END
        ),
        0
    ) AS sales_amount
FROM categories c
LEFT JOIN products p
    ON p.category_id = c.category_id
LEFT JOIN behavior_events e
    ON e.product_id = p.product_id
GROUP BY
    c.category_id,
    c.category_code;


-- ============================================================
-- User behavior summary
-- ============================================================
CREATE OR REPLACE VIEW v_user_behavior_summary AS
SELECT
    u.user_id,
    COUNT(e.event_id) AS event_count,
    COUNT(CASE WHEN e.event_type = 'view' THEN 1 END) AS view_count,
    COUNT(CASE WHEN e.event_type = 'cart' THEN 1 END) AS cart_count,
    COUNT(CASE WHEN e.event_type = 'purchase' THEN 1 END) AS purchase_count,
    COUNT(DISTINCT e.session_id) AS session_count,
    COALESCE(
        SUM(
            CASE
                WHEN e.event_type = 'purchase'
                THEN e.price
                ELSE 0
            END
        ),
        0
    ) AS purchase_amount
FROM users u
LEFT JOIN behavior_events e
    ON e.user_id = u.user_id
GROUP BY u.user_id;