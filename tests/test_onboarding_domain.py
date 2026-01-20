import uuid
from app.models.user import User
from app.models.domain import DomainQuestion


def test_onboarding_domain_flow(db, client):
    # 1. Seed a user directly in DB
    random_email = f"pytest_{uuid.uuid4().hex[:6]}@example.com"
    user = User(email=random_email, name="Pytest User", subscription_status="inactive")
    db.add(user)
    db.commit()
    db.refresh(user)

    # 2. Create onboarding session via API
    response = client.post("/api/v1/onboarding/sessions")
    assert response.status_code == 200
    session_id = response.json()["id"]

    # 3. Select domain via API
    response = client.patch(f"/api/v1/onboarding/sessions/{session_id}/domain", params={"domain": "facial"})
    assert response.status_code == 200

    # 4. Confirm payment via API
    response = client.patch(f"/api/v1/onboarding/sessions/{session_id}/payment")
    assert response.status_code == 200

    # 5. Link session to user via API
    response = client.patch(f"/api/v1/onboarding/sessions/{session_id}/link", params={"user_id": user.id})
    assert response.status_code == 200

    # 6. Seed domain questions directly in DB
    questions = [
        DomainQuestion(domain="facial", question="Do you exercise daily?", type="choice", options=["Yes", "No"], seq=1),
        DomainQuestion(domain="facial", question="Do you sleep well?", type="choice", options=["Yes", "No"], seq=2),
    ]
    db.add_all(questions)
    db.commit()

    # 7. Fetch domain flow via API
    response = client.get(f"/api/v1/domains/facial/flow", params={"user_id": user.id, "index": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["current"]["question"] == "Do you exercise daily?"


def test_invalid_domain_selection(client):
    # Create onboarding session
    response = client.post("/api/v1/onboarding/sessions")
    assert response.status_code == 200
    session_id = response.json()["id"]

    # Try selecting an invalid domain
    response = client.patch(f"/api/v1/onboarding/sessions/{session_id}/domain", params={"domain": "invalid_domain"})
    assert response.status_code == 422


def test_get_domain_progress(db, client):
    # Seed a user
    random_email = f"pytest_{uuid.uuid4().hex[:6]}@example.com"
    user = User(email=random_email, name="Progress Tester", subscription_status="inactive")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Fetch progress for a valid domain
    response = client.get(f"/api/v1/domains/facial/progress", params={"user_id": user.id})
    assert response.status_code == 200
    data = response.json()
    assert "progress" in data

