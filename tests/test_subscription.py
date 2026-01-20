from app.models.user import User


def test_create_subscription(client, db):
    # Seed a user first
    user = User(email="sub@example.com", name="Sub Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    payload = {"user_id": user.id, "plan": "monthly"}
    response = client.post("/api/v1/subscriptions/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "monthly"
    assert data["status"] == "active"
    assert data["user_id"] == user.id


def test_get_user_subscription(client, db):
    # Seed a user
    user = User(email="fetchsub@example.com", name="FetchSub Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create subscription
    payload = {"user_id": user.id, "plan": "weekly"}
    client.post("/api/v1/subscriptions/", json=payload)

    # Fetch subscription
    response = client.get(f"/api/v1/subscriptions/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["plan"] == "weekly"


def test_cancel_subscription(client, db):
    # Seed a user
    user = User(email="cancel@example.com", name="Cancel Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create subscription
    payload = {"user_id": user.id, "plan": "yearly"}
    response = client.post("/api/v1/subscriptions/", json=payload)
    sub_id = response.json()["id"]

    # Cancel subscription
    response = client.patch(f"/api/v1/subscriptions/{sub_id}/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


def test_get_subscription_nonexistent_user(client):
    # Try to fetch subscription for a non-existent user
    response = client.get("/api/v1/subscriptions/users/9999")
    assert response.status_code == 404

