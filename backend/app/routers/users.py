from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database import get_db


router = APIRouter()


@router.get("/{user_id}/events")
def user_events(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: str | None = None,
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size

    count_sql = text(
        """
        SELECT COUNT(*)
        FROM behavior_events
        WHERE user_id = :user_id
          AND (
              :event_type IS NULL
              OR event_type = :event_type
          )
        """
    )

    total = db.execute(
        count_sql,
        {
            "user_id": user_id,
            "event_type": event_type,
        },
    ).scalar_one()

    sql = text(
        """
        SELECT
            e.event_id,
            e.event_time,
            e.event_type,
            e.product_id,
            e.price,
            e.session_id,
            b.brand_name,
            c.category_code
        FROM behavior_events e
        LEFT JOIN brands b
            ON b.brand_id = e.brand_id
        LEFT JOIN products p
            ON p.product_id = e.product_id
        LEFT JOIN categories c
            ON c.category_id = p.category_id
        WHERE e.user_id = :user_id
          AND (
              :event_type IS NULL
              OR e.event_type = :event_type
          )
        ORDER BY e.event_time DESC
        LIMIT :limit OFFSET :offset
        """
    )

    rows = db.execute(
        sql,
        {
            "user_id": user_id,
            "event_type": event_type,
            "limit": page_size,
            "offset": offset,
        },
    ).mappings().all()

    if total == 0:
        raise HTTPException(
            status_code=404,
            detail="User not found or no matching events",
        )

    return {
        "user_id": user_id,
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [dict(row) for row in rows],
    }