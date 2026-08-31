from decimal import Decimal

from app.models import Product
from tests.conftest import TestingSessionLocal


def seed_products():
    with TestingSessionLocal() as db:
        db.add_all([
            Product(product_id="P1", name="Item 1", available_stock=10, unit_price=Decimal("100.00"), tax_percentage=Decimal("10.00")),
            Product(product_id="P2", name="Item 2", available_stock=5, unit_price=Decimal("50.00"), tax_percentage=Decimal("0.00")),
        ])
        db.commit()


def denominations():
    return [{"value": v, "count": 10} for v in [500, 50, 20, 10, 5, 2, 1]]


def test_create_bill_calculates_tax_and_decrements_stock(client):
    seed_products()
    response = client.post("/api/bills", json={
        "customer_email": "customer@example.com",
        "items": [{"product_id": "P1", "quantity": 2}, {"product_id": "P2", "quantity": 1}],
        "denominations": denominations(),
        "amount_paid": "300.00",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["total_before_tax"] == "250.00"
    assert data["total_tax"] == "20.00"
    assert data["net_payable"] == "270.00"
    assert data["change_due"] == "30.00"
    assert sum(v * k for k, v in ((int(k), v) for k, v in data["change_denominations"].items())) == 30

    with TestingSessionLocal() as db:
        assert db.get(Product, "P1").available_stock == 8


def test_insufficient_stock_does_not_create_bill(client):
    seed_products()
    response = client.post("/api/bills", json={
        "customer_email": "customer@example.com",
        "items": [{"product_id": "P1", "quantity": 11}],
        "denominations": denominations(),
        "amount_paid": "2000.00",
    })
    assert response.status_code == 409


def test_limited_denominations_find_exact_combination(client):
    seed_products()
    limited = [
        {"value": 500, "count": 0}, {"value": 50, "count": 0}, {"value": 20, "count": 1},
        {"value": 10, "count": 0}, {"value": 5, "count": 1}, {"value": 2, "count": 0}, {"value": 1, "count": 0},
    ]
    response = client.post("/api/bills", json={
        "customer_email": "customer@example.com",
        "items": [{"product_id": "P2", "quantity": 1}],
        "denominations": limited,
        "amount_paid": "75.00",
    })
    assert response.status_code == 201
    assert response.json()["change_denominations"] == {"20": 1, "5": 1}


def test_impossible_change_is_rejected(client):
    seed_products()
    limited = [{"value": v, "count": 0} for v in [500, 50, 20, 10, 5, 2, 1]]
    response = client.post("/api/bills", json={
        "customer_email": "customer@example.com",
        "items": [{"product_id": "P2", "quantity": 1}],
        "denominations": limited,
        "amount_paid": "100.00",
    })
    assert response.status_code == 409


def test_purchase_history_by_email(client):
    seed_products()
    payload = {
        "customer_email": "customer@example.com",
        "items": [{"product_id": "P2", "quantity": 1}],
        "denominations": denominations(),
        "amount_paid": "50.00",
    }
    assert client.post("/api/bills", json=payload).status_code == 201
    response = client.get("/api/purchases?email=customer@example.com")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["items"][0]["product_id"] == "P2"


def test_product_crud(client):
    payload = {"product_id": "P9", "name": "Test", "available_stock": 3, "unit_price": "99.99", "tax_percentage": "5"}
    assert client.post("/api/products", json=payload).status_code == 201
    response = client.get("/api/products/P9")
    assert response.json()["name"] == "Test"
    assert client.put("/api/products/P9", json={**payload, "name": "Updated"}).status_code == 200
    assert client.get("/api/products/P9").json()["name"] == "Updated"
    assert client.delete("/api/products/P9").status_code == 204
