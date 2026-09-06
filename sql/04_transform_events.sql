USE ecommerce;

-- ============================================================
-- Transform staging events into behavior_events
--
-- Exact duplicate events are removed by source_event_hash.
-- brand is converted to brand_id through the brands table.
-- user_session may be NULL.
-- ============================================================

INSERT IGNORE INTO behavior_events (
    event_time,
    event_type,
    user_id,
    session_id,
    product_id,
    brand_id,
    price,
    source_event_hash
)
SELECT
    STR_TO_DATE(
        REPLACE(s.event_time_raw, ' UTC', ''),
        '%Y-%m-%d %H:%i:%s'
    ) AS event_time,

    s.event_type,

    s.user_id,

    NULLIF(s.user_session, '') AS session_id,

    s.product_id,

    b.brand_id,

    s.price,

    UNHEX(
        SHA2(
            CONCAT_WS(
                CHAR(31),
                s.event_time_raw,
                s.event_type,
                s.product_id,
                s.category_id,
                COALESCE(s.category_code, ''),
                COALESCE(s.brand, ''),
                s.price,
                s.user_id,
                COALESCE(s.user_session, '')
            ),
            256
        )
    ) AS source_event_hash

FROM staging_events s

LEFT JOIN brands b
    ON b.brand_name = TRIM(s.brand);