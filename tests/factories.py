"""Small helpers that create resources through the public API."""

from itertools import count
from typing import Any

from fastapi.testclient import TestClient

_sequence = count(1)


def create_plan(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"name": "Pro", "billing_cycle": "monthly", "price": "100.00", "currency": "USD"}
    payload.update(overrides)
    response = client.post("/plans", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def create_customer(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"name": "Ada Lovelace", "email": f"customer{next(_sequence)}@example.com"}
    payload.update(overrides)
    response = client.post("/customers", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def create_subscription(client: TestClient, customer_id: int, plan_id: int) -> dict[str, Any]:
    response = client.post("/subscriptions", json={"customer_id": customer_id, "plan_id": plan_id})
    assert response.status_code == 201, response.text
    return response.json()


def create_invoice(client: TestClient, price: str = "100.00") -> dict[str, Any]:
    """Create plan -> customer -> subscription -> invoice and return the invoice."""
    plan = create_plan(client, price=price)
    customer = create_customer(client)
    subscription = create_subscription(client, customer["id"], plan["id"])
    response = client.post("/invoices/generate", json={"subscription_id": subscription["id"]})
    assert response.status_code == 201, response.text
    return response.json()


def record_payment(client: TestClient, invoice_id: int, amount: str, status: str = "success", **extra: Any):
    payload = {"invoice_id": invoice_id, "amount": amount, "status": status, **extra}
    return client.post("/payments/record", json=payload)
