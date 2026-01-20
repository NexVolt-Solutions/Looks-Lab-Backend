from app.models.user import User
from app.models.insight import Insight


def test_create_insight(client, db):
    # Seed a user first
    user = User(email="insight@example.com", name="Insight Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    payload = {
        "user_id": user.id,
        "category": "health",
        "content": "Stay hydrated",
        "source": "system",
    }
    response = client.post("/api/v1/insights/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Stay hydrated"
    assert data["user_id"] == user.id


def test_get_user_insights(client, db):
    # Seed a user and an insight directly
    user = User(email="insfetch@example.com", name="Insight Fetch Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    insight = Insight(user_id=user.id, category="facial", content="Exercise daily", source="system")
    db.add(insight)
    db.commit()
    db.refresh(insight)

    response = client.get(f"/api/v1/insights/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["content"] == "Exercise daily"


def test_delete_insight(client, db):
    # Seed a user and an insight directly
    user = User(email="insdel@example.com", name="Insight Del Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    insight = Insight(user_id=user.id, category="health", content="Drink water", source="system")
    db.add(insight)
    db.commit()
    db.refresh(insight)

    # Delete insight
    response = client.delete(f"/api/v1/insights/{insight.id}")
    assert response.status_code == 200

    # Verify deletion
    response = client.get(f"/api/v1/insights/users/{user.id}")
    assert response.status_code == 200
    assert response.json() == []


def test_get_nonexistent_insight(client):
    # Try to fetch an insight that doesn't exist
    response = client.get("/api/v1/insights/9999")
    assert response.status_code == 404

