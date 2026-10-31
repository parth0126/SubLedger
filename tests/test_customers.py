from tests.factories import create_customer


def test_duplicate_customer_email_is_rejected(client):
    create_customer(client, email="billing@acme.io")

    response = client.post("/customers", json={"name": "Someone Else", "email": "billing@acme.io"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert len(client.get("/customers").json()) == 1


def test_duplicate_email_check_is_case_insensitive(client):
    create_customer(client, email="billing@acme.io")

    response = client.post("/customers", json={"name": "Shouty", "email": "BILLING@ACME.IO"})

    assert response.status_code == 409


def test_create_and_fetch_customer(client):
    customer = create_customer(
        client, company="Acme", contact_details={"phone": "+1-555-0100"}
    )

    response = client.get(f"/customers/{customer['id']}")

    assert response.status_code == 200
    assert response.json()["company"] == "Acme"
    assert response.json()["contact_details"] == {"phone": "+1-555-0100"}


def test_fetch_unknown_customer_returns_404(client):
    assert client.get("/customers/12345").status_code == 404
