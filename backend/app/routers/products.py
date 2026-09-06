from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database import get_db


router = APIRouter()


@router.get("")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size

    count_sql = text(
        """
        SELECT COUNT(*)
        FROM products
        """
    )

    total = db.execute(count_sql).scalar_one()

    sql = text(
        """
        SELECT
            p.product_id,
            p.category_id,
            c.category_code
        FROM products p
        LEFT JOIN categories c
            ON c.category_id = p.category_id
        ORDER BY p.product_id
        LIMIT :limit OFFSET :offset
        """
    )

    rows = (
        db.execute(
            sql,
            {
                "limit": page_size,
                "offset": offset,
            },
        )
        .mappings()
        .all()
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [dict(row) for row in rows],
    }


@router.get("/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT
            p.product_id,
            p.category_id,
            c.category_code
        FROM products p
        LEFT JOIN categories c
            ON c.category_id = p.category_id
        WHERE p.product_id = :product_id
        """
    )

    row = (
        db.execute(
            sql,
            {"product_id": product_id},
        )
        .mappings()
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    brand_sql = text(
        """
        SELECT
            b.brand_id,
            b.brand_name
        FROM product_brands pb
        JOIN brands b
            ON b.brand_id = pb.brand_id
        WHERE pb.product_id = :product_id
        ORDER BY b.brand_name
        """
    )

    brands = (
        db.execute(
            brand_sql,
            {"product_id": product_id},
        )
        .mappings()
        .all()
    )

    result = dict(row)
    result["brands"] = [dict(brand) for brand in brands]

    return result


@router.get("/{product_id}/statistics")
def product_statistics(
    product_id: int,
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT
            product_id,
            category_id,
            category_code,
            event_count,
            view_count,
            cart_count,
            purchase_count,
            sales_amount
        FROM v_product_statistics
        WHERE product_id = :product_id
        """
    )

    row = (
        db.execute(
            sql,
            {"product_id": product_id},
        )
        .mappings()
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return dict(row)