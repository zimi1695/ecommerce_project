from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database import get_db


router = APIRouter()


@router.get("/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    session_sql = text(
        """
        SELECT
            session_id,
            start_time,
            end_time,
            event_count
        FROM sessions
        WHERE session_id = :session_id
        """
    )

    session_row = (
        db.execute(
            session_sql,
            {"session_id": session_id},
        )
        .mappings()
        .first()
    )

    if session_row is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    events_sql = text(
        """
        SELECT
            e.event_id,
            e.event_time,
            e.event_type,
            e.user_id,
            e.product_id,
            e.price,
            b.brand_name,
            c.category_code
        FROM behavior_events e
        LEFT JOIN brands b
            ON b.brand_id = e.brand_id
        LEFT JOIN products p
            ON p.product_id = e.product_id
        LEFT JOIN categories c
            ON c.category_id = p.category_id
        WHERE e.session_id = :session_id
        ORDER BY e.event_time
        """
    )

    events = (
        db.execute(
            events_sql,
            {"session_id": session_id},
        )
        .mappings()
        .all()
    )

    result = dict(session_row)
    result["events"] = [dict(event) for event in events]

    return result