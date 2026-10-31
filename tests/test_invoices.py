from datetime import date

from app.models.enums import BillingCycle
from app.services.billing_period import period_end
from tests.factories import create_customer, create_invoice, create_plan, create_subscription


def test_invoice_uses_plan_price_at_generation_time(client):
    plan = create_plan(client, price="100.00")
    customer = create_customer(client)
    subscription = create_subscription(client, customer["id"], plan["id"])

    invoice = client.post("/invoices/generate", json={"subscription_id": subscription["id"]}).json()
    client.patch(f"/plans/{plan['id']}", json={"price": "250.00"})

    fetched = client.get(f"/invoices/{invoice['id']}").json()
    assert invoice["amount_due"] == "100.00"
    assert fetched["amount_due"] == "100.00"
    assert fetched["amount_paid"] == "0.00"
    assert fetched["status"] == "issued"
    assert fetched["period_start"] == subscription["current_period_start"]
    assert fetched["period_end"] == subscription["current_period_end"]


def test_invoice_generation_writes_ledger_entry(client):
    invoice = create_invoice(client, price="49.50")

    ledger = client.get(f"/customers/{invoice['customer_id']}/ledger").json()

    assert len(ledger) == 1
    assert ledger[0]["entry_type"] == "invoice_created"
    assert ledger[0]["amount"] == "49.50"
    assert ledger[0]["reference_id"] == f"invoice:{invoice['id']}"


def test_current_period_cannot_be_invoiced_twice(client):
    invoice = create_invoice(client)

    response = client.post("/invoices/generate", json={"subscription_id": invoice["subscription_id"]})

    assert response.status_code == 409


def test_cannot_invoice_cancelled_subscription(client):
    plan = create_plan(client)
    customer = create_customer(client)
    subscription = create_subscription(client, customer["id"], plan["id"])
    client.post(f"/subscriptions/{subscription['id']}/cancel")

    response = client.post("/invoices/generate", json={"subscription_id": subscription["id"]})

    assert response.status_code == 422


def test_elapsed_period_is_renewed_on_next_invoice(client):
    plan = create_plan(client, price="10.00")
    customer = create_customer(client)
    subscription = client.post(
        "/subscriptions",
        json={"customer_id": customer["id"], "plan_id": plan["id"], "start_date": "2020-01-15"},
    ).json()
    first = client.post("/invoices/generate", json={"subscription_id": subscription["id"]}).json()
    client.patch(f"/plans/{plan['id']}", json={"price": "12.00"})

    second = client.post("/invoices/generate", json={"subscription_id": subscription["id"]})

    assert second.status_code == 201
    assert first["period_start"] == "2020-01-15"
    assert second.json()["period_start"] == "2020-02-15"
    assert second.json()["amount_due"] == "12.00"


def test_unknown_invoice_returns_404(client):
    assert client.get("/invoices/999").status_code == 404


def test_period_end_clamps_to_month_length():
    assert period_end(date(2026, 1, 31), BillingCycle.MONTHLY) == date(2026, 2, 28)
    assert period_end(date(2026, 11, 30), BillingCycle.QUARTERLY) == date(2027, 2, 28)
    assert period_end(date(2028, 2, 29), BillingCycle.YEARLY) == date(2029, 2, 28)
