from tests.factories import create_invoice, record_payment


def test_full_successful_payment_marks_invoice_paid(client):
    invoice = create_invoice(client, price="100.00")

    response = record_payment(client, invoice["id"], "100.00", provider_reference="ch_123")

    assert response.status_code == 201
    body = response.json()
    assert body["payment"]["status"] == "success"
    assert body["payment"]["provider_reference"] == "ch_123"
    assert body["invoice"]["amount_paid"] == "100.00"
    assert body["invoice"]["balance_due"] == "0.00"
    assert body["invoice"]["status"] == "paid"


def test_partial_payments_mark_invoice_partially_paid_then_paid(client):
    invoice = create_invoice(client, price="100.00")

    first = record_payment(client, invoice["id"], "40.00").json()["invoice"]
    second = record_payment(client, invoice["id"], "60.00").json()["invoice"]

    assert first["status"] == "partially_paid"
    assert first["amount_paid"] == "40.00"
    assert second["status"] == "paid"
    assert second["amount_paid"] == "100.00"


def test_failed_payment_does_not_change_amount_paid(client):
    invoice = create_invoice(client, price="100.00")
    record_payment(client, invoice["id"], "30.00")

    response = record_payment(
        client, invoice["id"], "50.00", status="failed", failure_reason="card_declined"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["payment"]["status"] == "failed"
    assert body["payment"]["failure_reason"] == "card_declined"
    assert body["invoice"]["amount_paid"] == "30.00"
    assert body["invoice"]["status"] == "partially_paid"
    stored = client.get(f"/invoices/{invoice['id']}").json()
    assert stored["amount_paid"] == "30.00"
    assert [p["status"] for p in stored["payment_attempts"]] == ["success", "failed"]


def test_failed_payment_requires_reason(client):
    invoice = create_invoice(client)

    response = record_payment(client, invoice["id"], "10.00", status="failed")

    assert response.status_code == 422


def test_payment_exceeding_remaining_balance_fails(client):
    invoice = create_invoice(client, price="100.00")
    record_payment(client, invoice["id"], "70.00")

    response = record_payment(client, invoice["id"], "30.01")

    assert response.status_code == 422
    assert "exceeds the remaining invoice balance" in response.json()["error"]["message"]
    stored = client.get(f"/invoices/{invoice['id']}").json()
    assert stored["amount_paid"] == "70.00"
    assert len(stored["payment_attempts"]) == 1


def test_paid_invoice_rejects_further_payments(client):
    invoice = create_invoice(client, price="100.00")
    record_payment(client, invoice["id"], "100.00")

    response = record_payment(client, invoice["id"], "1.00")

    assert response.status_code == 422


def test_non_positive_payment_amount_fails(client):
    invoice = create_invoice(client)

    assert record_payment(client, invoice["id"], "0").status_code == 422
    assert record_payment(client, invoice["id"], "-5.00").status_code == 422


def test_payment_currency_must_match_invoice(client):
    invoice = create_invoice(client)

    response = record_payment(client, invoice["id"], "10.00", currency="EUR")

    assert response.status_code == 422


def test_payment_against_unknown_invoice_returns_404(client):
    assert record_payment(client, 999, "10.00").status_code == 404
