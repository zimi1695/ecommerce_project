from sqlalchemy import text

from backend.app.database import SessionLocal


def get_db():
    return SessionLocal()


def test_no_duplicate_event_hash():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS total,
                       COUNT(DISTINCT source_event_hash) AS distinct_hashes
                FROM behavior_events
                """
            )
        ).mappings().one()

        assert row["total"] == row["distinct_hashes"]

    finally:
        db.close()


def test_products_have_valid_categories():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS orphan_count
                FROM products p
                LEFT JOIN categories c
                    ON c.category_id = p.category_id
                WHERE c.category_id IS NULL
                """
            )
        ).mappings().one()

        assert row["orphan_count"] == 0

    finally:
        db.close()


def test_product_brands_have_valid_products():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS orphan_count
                FROM product_brands pb
                LEFT JOIN products p
                    ON p.product_id = pb.product_id
                WHERE p.product_id IS NULL
                """
            )
        ).mappings().one()

        assert row["orphan_count"] == 0

    finally:
        db.close()


def test_product_brands_have_valid_brands():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS orphan_count
                FROM product_brands pb
                LEFT JOIN brands b
                    ON b.brand_id = pb.brand_id
                WHERE b.brand_id IS NULL
                """
            )
        ).mappings().one()

        assert row["orphan_count"] == 0

    finally:
        db.close()


def test_event_type_values():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS invalid_count
                FROM behavior_events
                WHERE event_type NOT IN (
                    'view',
                    'cart',
                    'purchase'
                )
                """
            )
        ).mappings().one()

        assert row["invalid_count"] == 0

    finally:
        db.close()


def test_event_price_non_negative():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS invalid_count
                FROM behavior_events
                WHERE price < 0
                """
            )
        ).mappings().one()

        assert row["invalid_count"] == 0

    finally:
        db.close()


def test_business_views_exist():
    db = get_db()

    try:
        rows = db.execute(
            text(
                """
                SHOW FULL TABLES
                WHERE Table_type = 'VIEW'
                """
            )
        ).all()

        view_names = {row[0] for row in rows}

        required_views = {
            "v_product_statistics",
            "v_brand_statistics",
            "v_category_statistics",
            "v_user_behavior_summary",
        }

        assert required_views.issubset(view_names)

    finally:
        db.close()


def test_product_statistics_view_queryable():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS total
                FROM v_product_statistics
                """
            )
        ).mappings().one()

        assert row["total"] >= 0

    finally:
        db.close()


def test_brand_statistics_view_queryable():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS total
                FROM v_brand_statistics
                """
            )
        ).mappings().one()

        assert row["total"] >= 0

    finally:
        db.close()


def test_category_statistics_view_queryable():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS total
                FROM v_category_statistics
                """
            )
        ).mappings().one()

        assert row["total"] >= 0

    finally:
        db.close()


def test_user_summary_view_queryable():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS total
                FROM v_user_behavior_summary
                """
            )
        ).mappings().one()

        assert row["total"] >= 0

    finally:
        db.close()

def test_required_event_fields_not_null():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS invalid_count
                FROM behavior_events
                WHERE event_time IS NULL
                   OR event_type IS NULL
                   OR user_id IS NULL
                   OR product_id IS NULL
                   OR price IS NULL
                   OR source_event_hash IS NULL
                """
            )
        ).mappings().one()

        assert row["invalid_count"] == 0

    finally:
        db.close()


def test_price_range_is_valid():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS invalid_count
                FROM behavior_events
                WHERE price < 0
                   OR price > 100000
                """
            )
        ).mappings().one()

        assert row["invalid_count"] == 0

    finally:
        db.close()


def test_users_have_valid_ids():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS invalid_count
                FROM users
                WHERE user_id <= 0
                """
            )
        ).mappings().one()

        assert row["invalid_count"] == 0

    finally:
        db.close()


def test_products_have_valid_ids():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS invalid_count
                FROM products
                WHERE product_id <= 0
                   OR category_id <= 0
                """
            )
        ).mappings().one()

        assert row["invalid_count"] == 0

    finally:
        db.close()


def test_event_time_range_is_valid():
    db = get_db()

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS invalid_count
                FROM behavior_events
                WHERE event_time < '2019-11-01 00:00:00'
                   OR event_time >= '2019-12-01 00:00:00'
                """
            )
        ).mappings().one()

        assert row["invalid_count"] == 0

    finally:
        db.close()