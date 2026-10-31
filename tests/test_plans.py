from decimal import Decimal

import pytest

from app.core.exceptions import BusinessRuleViolation
from app.repositories import PlanRepository
from app.schemas.plan import PlanCreate
from app.services import PlanService
from tests.factories import create_plan


@pytest.mark.parametrize("price", ["0", "0.00", "-10.00"])
def test_create_plan_with_non_positive_price_fails(client, price):
    response = client.post(
        "/plans", json={"name": "Free?", "billing_cycle": "monthly", "price": price}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert client.get("/plans").json() == []


def test_plan_service_rejects_non_positive_price_even_without_schema_validation(db_session):
    service = PlanService(db_session, PlanRepository(db_session))
    data = PlanCreate.model_construct(
        name="Broken", description=None, billing_cycle="monthly", price=Decimal("0"),
        currency="USD", status="active",
    )

    with pytest.raises(BusinessRuleViolation):
        service.create_plan(data)


def test_create_and_list_plans(client):
    plan = create_plan(client, name="Starter", price="9.99", currency="eur")

    assert plan["price"] == "9.99"
    assert plan["currency"] == "EUR"
    assert plan["status"] == "active"
    assert [p["id"] for p in client.get("/plans").json()] == [plan["id"]]


def test_update_plan_price_and_deactivate(client):
    plan = create_plan(client)

    response = client.patch(f"/plans/{plan['id']}", json={"price": "120.00", "status": "inactive"})

    assert response.status_code == 200
    assert response.json()["price"] == "120.00"
    assert response.json()["status"] == "inactive"


def test_update_plan_rejects_non_positive_price(client):
    plan = create_plan(client)

    response = client.patch(f"/plans/{plan['id']}", json={"price": "0"})

    assert response.status_code == 422


def test_update_unknown_plan_returns_404(client):
    response = client.patch("/plans/999", json={"name": "Ghost"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
