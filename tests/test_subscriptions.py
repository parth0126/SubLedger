from tests.factories import create_customer, create_plan, create_subscription


def test_subscription_to_inactive_plan_fails(client):
    plan = create_plan(client, status="inactive")
    customer = create_customer(client)

    response = client.post(
        "/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "business_rule_violation"


def test_duplicate_active_subscription_to_same_plan_fails(client):
    plan = create_plan(client)
    customer = create_customer(client)
    create_subscription(client, customer["id"], plan["id"])

    response = client.post(
        "/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]}
    )

    assert response.status_code == 409
    assert len(client.get("/subscriptions", params={"customer_id": customer["id"]}).json()) == 1


def test_customer_can_resubscribe_after_cancelling(client):
    plan = create_plan(client)
    customer = create_customer(client)
    first = create_subscription(client, customer["id"], plan["id"])

    cancel = client.post(f"/subscriptions/{first['id']}/cancel")
    second = client.post(
        "/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]}
    )

    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    assert cancel.json()["cancelled_at"] is not None
    assert second.status_code == 201


def test_cancelling_twice_conflicts(client):
    plan = create_plan(client)
    customer = create_customer(client)
    subscription = create_subscription(client, customer["id"], plan["id"])
    client.post(f"/subscriptions/{subscription['id']}/cancel")

    response = client.post(f"/subscriptions/{subscription['id']}/cancel")

    assert response.status_code == 409


def test_subscription_period_follows_billing_cycle(client):
    plan = create_plan(client, billing_cycle="yearly")
    customer = create_customer(client)

    response = client.post(
        "/subscriptions",
        json={"customer_id": customer["id"], "plan_id": plan["id"], "start_date": "2026-01-31"},
    )

    body = response.json()
    assert body["current_period_start"] == "2026-01-31"
    assert body["current_period_end"] == "2027-01-31"
