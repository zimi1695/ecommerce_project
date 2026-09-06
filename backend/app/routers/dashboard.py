from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database import get_db


router = APIRouter()


@router.get("/overview")
def dashboard_overview(
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT
            (SELECT COUNT(*) FROM users) AS total_users,
            (SELECT COUNT(*) FROM products) AS total_products,
            (SELECT COUNT(*) FROM categories) AS total_categories,
            (SELECT COUNT(*) FROM brands) AS total_brands,
            (SELECT COUNT(*) FROM behavior_events) AS total_events,
            (
                SELECT COUNT(*)
                FROM behavior_events
                WHERE event_type = 'view'
            ) AS total_views,
            (
                SELECT COUNT(*)
                FROM behavior_events
                WHERE event_type = 'cart'
            ) AS total_carts,
            (
                SELECT COUNT(*)
                FROM behavior_events
                WHERE event_type = 'purchase'
            ) AS total_purchases
        """
    )

    row = db.execute(sql).mappings().one()

    return dict(row)