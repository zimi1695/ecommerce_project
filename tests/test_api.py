import pytest

from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.main import app
from backend.app.database import SessionLocal


client = TestClient(app)


def get_first_user_id():
    db = SessionLocal()

    try:
        row = db.execute(
            text(
                """
                SELECT user_id
                FROM users
                LIMIT 1
                """
            )
        ).first()

        return row[0] if row else None

    finally:
        db.close()


def get_first_session_id():
    db = SessionLocal()

    try:
        row = db.execute(
            text(
                """
                SELECT session_id
                FROM sessions
                ORDER BY event_count DESC
                LIMIT 1
                """
            )
        ).first()

        return row[0] if row else None

    finally:
        db.close()


def get_first_product_id():
    db = SessionLocal()

    try:
        row = db.execute(
            text(
                """
                SELECT product_id
                FROM products
                ORDER BY product_id
                LIMIT 1
                """
            )
        ).first()

        return row[0] if row else None

    finally:
        db.close()


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == (
        "E-commerce User Behavior Analysis System"
    )
    assert data["status"] == "running"


def test_dashboard_overview():
    response = client.get(
        "/api/dashboard/overview"
    )

    assert response.status_code == 200

    data = response.json()

    required_fields = {
        "total_users",
        "total_products",
        "total_categories",
        "total_brands",
        "total_events",
        "total_views",
        "total_carts",
        "total_purchases",
    }

    assert required_fields.issubset(data.keys())

    for field in required_fields:
        assert data[field] >= 0


def test_product_list():
    response = client.get(
        "/api/products",
        params={
            "page": 1,
            "page_size": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 5
    assert "total" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 5


def test_product_list_pagination_validation():
    response = client.get(
        "/api/products",
        params={
            "page": 0,
            "page_size": 5,
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["code"] == 422
    assert data["message"] == "Request validation failed"
    assert data["data"] is not None

    response = client.get(
        "/api/products",
        params={
            "page": 1,
            "page_size": 101,
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["code"] == 422
    assert data["message"] == "Request validation failed"
    assert data["data"] is not None


def test_product_detail():
    product_id = get_first_product_id()

    if product_id is None:
        pytest.skip("No products available")

    response = client.get(
        f"/api/products/{product_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id
    assert "category_id" in data
    assert "category_code" in data
    assert "brands" in data
    assert isinstance(data["brands"], list)


def test_product_not_found():
    response = client.get(
        "/api/products/999999999999999999"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == 404
    assert data["message"] == "Product not found"
    assert data["data"] is None


def test_product_statistics():
    product_id = get_first_product_id()

    if product_id is None:
        pytest.skip("No products available")

    response = client.get(
        f"/api/products/{product_id}/statistics"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_id"] == product_id
    assert "event_count" in data
    assert "view_count" in data
    assert "cart_count" in data
    assert "purchase_count" in data
    assert "sales_amount" in data

    assert data["event_count"] >= 0
    assert data["view_count"] >= 0
    assert data["cart_count"] >= 0
    assert data["purchase_count"] >= 0
    assert data["sales_amount"] >= 0


def test_product_statistics_not_found():
    response = client.get(
        "/api/products/999999999999999999/statistics"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == 404
    assert data["message"] == "Product not found"
    assert data["data"] is None


def test_user_events():
    user_id = get_first_user_id()

    if user_id is None:
        pytest.skip("No users available")

    response = client.get(
        f"/api/users/{user_id}/events",
        params={
            "page": 1,
            "page_size": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user_id
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 5


def test_user_events_purchase_filter():
    db = SessionLocal()

    try:
        row = db.execute(
            text(
                """
                SELECT user_id
                FROM behavior_events
                WHERE event_type = 'purchase'
                LIMIT 1
                """
            )
        ).first()
    finally:
        db.close()

    if row is None:
        pytest.skip("No purchase events available")

    user_id = row[0]

    response = client.get(
        f"/api/users/{user_id}/events",
        params={
            "page": 1,
            "page_size": 5,
            "event_type": "purchase",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] > 0

    for item in data["items"]:
        assert item["event_type"] == "purchase"


def test_analytics_top_products():
    response = client.get(
        "/api/analytics/top-products",
        params={"limit": 5},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 5
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 5

    if data["items"]:
        item = data["items"][0]

        assert "product_id" in item
        assert "event_count" in item
        assert "purchase_count" in item
        assert "sales_amount" in item

        assert item["event_count"] >= 0
        assert item["purchase_count"] >= 0
        assert item["sales_amount"] >= 0


def test_analytics_top_brands():
    response = client.get(
        "/api/analytics/top-brands",
        params={"limit": 5},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 5
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 5


def test_analytics_top_categories():
    response = client.get(
        "/api/analytics/top-categories",
        params={"limit": 5},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 5
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 5


def test_conversion():
    response = client.get(
        "/api/analytics/conversion"
    )

    assert response.status_code == 200

    data = response.json()

    required_fields = {
        "total_sessions",
        "view_sessions",
        "cart_sessions",
        "purchase_sessions",
        "view_cart_sessions",
        "cart_purchase_sessions",
        "view_purchase_sessions",
        "view_to_cart_rate",
        "cart_to_purchase_rate",
        "view_to_purchase_rate",
    }

    assert required_fields.issubset(data.keys())

    assert data["total_sessions"] >= 0
    assert data["view_sessions"] >= 0
    assert data["cart_sessions"] >= 0
    assert data["purchase_sessions"] >= 0

    assert data["view_cart_sessions"] >= 0
    assert data["cart_purchase_sessions"] >= 0
    assert data["view_purchase_sessions"] >= 0

    assert 0 <= data["view_to_cart_rate"] <= 1
    assert 0 <= data["cart_to_purchase_rate"] <= 1
    assert 0 <= data["view_to_purchase_rate"] <= 1

    assert (
        data["view_cart_sessions"]
        <= data["view_sessions"]
    )

    assert (
        data["cart_purchase_sessions"]
        <= data["cart_sessions"]
    )

    assert (
        data["view_purchase_sessions"]
        <= data["view_sessions"]
    )


def test_session_detail():
    session_id = get_first_session_id()

    if session_id is None:
        pytest.skip("No sessions available")

    response = client.get(
        f"/api/sessions/{session_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == session_id
    assert "start_time" in data
    assert "end_time" in data
    assert "event_count" in data
    assert "events" in data
    assert isinstance(data["events"], list)


def test_session_not_found():
    response = client.get(
        "/api/sessions/"
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == 404
    assert data["message"] == "Session not found"
    assert data["data"] is None