from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database import get_db


router = APIRouter()


@router.get("/top-products")
def top_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT
            e.product_id,
            COUNT(*) AS event_count,
            COALESCE(
                SUM(
                    CASE
                        WHEN e.event_type = 'purchase'
                        THEN e.price
                        ELSE 0
                    END
                ),
                0
            ) AS sales_amount,
            COUNT(
                CASE
                    WHEN e.event_type = 'purchase'
                    THEN 1
                END
            ) AS purchase_count
        FROM behavior_events e
        GROUP BY e.product_id
        ORDER BY event_count DESC
        LIMIT :limit
        """
    )

    rows = (
        db.execute(
            sql,
            {"limit": limit},
        )
        .mappings()
        .all()
    )

    return {
        "limit": limit,
        "items": [dict(row) for row in rows],
    }


@router.get("/top-brands")
def top_brands(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT
            b.brand_id,
            b.brand_name,
            COUNT(*) AS event_count,
            COALESCE(
                SUM(
                    CASE
                        WHEN e.event_type = 'purchase'
                        THEN e.price
                        ELSE 0
                    END
                ),
                0
            ) AS sales_amount,
            COUNT(
                CASE
                    WHEN e.event_type = 'purchase'
                    THEN 1
                END
            ) AS purchase_count
        FROM behavior_events e
        JOIN brands b
            ON b.brand_id = e.brand_id
        GROUP BY
            b.brand_id,
            b.brand_name
        ORDER BY event_count DESC
        LIMIT :limit
        """
    )

    rows = (
        db.execute(
            sql,
            {"limit": limit},
        )
        .mappings()
        .all()
    )

    return {
        "limit": limit,
        "items": [dict(row) for row in rows],
    }


@router.get("/top-categories")
def top_categories(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT
            c.category_id,
            c.category_code,
            COUNT(*) AS event_count,
            COALESCE(
                SUM(
                    CASE
                        WHEN e.event_type = 'purchase'
                        THEN e.price
                        ELSE 0
                    END
                ),
                0
            ) AS sales_amount,
            COUNT(
                CASE
                    WHEN e.event_type = 'purchase'
                    THEN 1
                END
            ) AS purchase_count
        FROM behavior_events e
        JOIN products p
            ON p.product_id = e.product_id
        JOIN categories c
            ON c.category_id = p.category_id
        GROUP BY
            c.category_id,
            c.category_code
        ORDER BY event_count DESC
        LIMIT :limit
        """
    )

    rows = (
        db.execute(
            sql,
            {"limit": limit},
        )
        .mappings()
        .all()
    )

    return {
        "limit": limit,
        "items": [dict(row) for row in rows],
    }


@router.get("/conversion")
def conversion(
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT
            COUNT(*) AS total_sessions,

            SUM(
                CASE
                    WHEN has_view = 1
                    THEN 1
                    ELSE 0
                END
            ) AS view_sessions,

            SUM(
                CASE
                    WHEN has_cart = 1
                    THEN 1
                    ELSE 0
                END
            ) AS cart_sessions,

            SUM(
                CASE
                    WHEN has_purchase = 1
                    THEN 1
                    ELSE 0
                END
            ) AS purchase_sessions,

            SUM(
                CASE
                    WHEN has_view = 1
                     AND has_cart = 1
                    THEN 1
                    ELSE 0
                END
            ) AS view_cart_sessions,

            SUM(
                CASE
                    WHEN has_cart = 1
                     AND has_purchase = 1
                    THEN 1
                    ELSE 0
                END
            ) AS cart_purchase_sessions,

            SUM(
                CASE
                    WHEN has_view = 1
                     AND has_purchase = 1
                    THEN 1
                    ELSE 0
                END
            ) AS view_purchase_sessions

        FROM (
            SELECT
                session_id,

                MAX(
                    CASE
                        WHEN event_type = 'view'
                        THEN 1
                        ELSE 0
                    END
                ) AS has_view,

                MAX(
                    CASE
                        WHEN event_type = 'cart'
                        THEN 1
                        ELSE 0
                    END
                ) AS has_cart,

                MAX(
                    CASE
                        WHEN event_type = 'purchase'
                        THEN 1
                        ELSE 0
                    END
                ) AS has_purchase

            FROM behavior_events

            WHERE session_id IS NOT NULL

            GROUP BY session_id
        ) AS session_flags
        """
    )

    row = (
        db.execute(sql)
        .mappings()
        .one()
    )

    total_sessions = int(
        row["total_sessions"] or 0
    )

    view_sessions = int(
        row["view_sessions"] or 0
    )

    cart_sessions = int(
        row["cart_sessions"] or 0
    )

    purchase_sessions = int(
        row["purchase_sessions"] or 0
    )

    view_cart_sessions = int(
        row["view_cart_sessions"] or 0
    )

    cart_purchase_sessions = int(
        row["cart_purchase_sessions"] or 0
    )

    view_purchase_sessions = int(
        row["view_purchase_sessions"] or 0
    )

    return {
        "total_sessions": total_sessions,

        "view_sessions": view_sessions,
        "cart_sessions": cart_sessions,
        "purchase_sessions": purchase_sessions,

        "view_cart_sessions": view_cart_sessions,
        "cart_purchase_sessions": cart_purchase_sessions,
        "view_purchase_sessions": view_purchase_sessions,

        "view_to_cart_rate": (
            view_cart_sessions / view_sessions
            if view_sessions
            else 0
        ),

        "cart_to_purchase_rate": (
            cart_purchase_sessions / cart_sessions
            if cart_sessions
            else 0
        ),

        "view_to_purchase_rate": (
            view_purchase_sessions / view_sessions
            if view_sessions
            else 0
        ),
    }