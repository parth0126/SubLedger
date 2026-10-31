import pytest
from sqlalchemy import select

from app.core.exceptions import AppendOnlyViolation
from app.models import LedgerEntry
from tests.factories import create_invoice, record_payment


def test_ledger_history_records_all_events_in_order(client):
    invoice = create_invoice(client, price="100.00")
    success = record_payment(client, invoice["id"], "60.00").json()["payment"]
    failure = record_payment(
        client, invoice["id"], "40.00", status="failed", failure_reason="insufficient_funds"
    ).json()["payment"]

    response = client.get(f"/customers/{invoice['customer_id']}/ledger")

    assert response.status_code == 200
    entries = response.json()
    assert [(e["entry_type"], e["reference_id"], e["amount"]) for e in entries] == [
        ("invoice_created", f"invoice:{invoice['id']}", "100.00"),
        ("payment_success", f"payment_attempt:{success['id']}", "60.00"),
        ("payment_failure", f"payment_attempt:{failure['id']}", "40.00"),
    ]
    assert all(e["invoice_id"] == invoice["id"] for e in entries)
    assert "insufficient_funds" in entries[2]["description"]


def test_rejected_payment_writes_no_ledger_entry(client):
    invoice = create_invoice(client, price="100.00")

    record_payment(client, invoice["id"], "150.00")

    entries = client.get(f"/customers/{invoice['customer_id']}/ledger").json()
    assert [e["entry_type"] for e in entries] == ["invoice_created"]


def test_ledger_for_unknown_customer_returns_404(client):
    assert client.get("/customers/999/ledger").status_code == 404


def test_ledger_entries_cannot_be_updated(client, db_session):
    create_invoice(client)
    entry = db_session.scalars(select(LedgerEntry)).one()

    entry.description = "tampered"
    with pytest.raises(AppendOnlyViolation):
        db_session.flush()


def test_ledger_entries_cannot_be_deleted(client, db_session):
    create_invoice(client)
    entry = db_session.scalars(select(LedgerEntry)).one()

    db_session.delete(entry)
    with pytest.raises(AppendOnlyViolation):
        db_session.flush()
