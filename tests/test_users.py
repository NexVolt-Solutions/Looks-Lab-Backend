def test_create_and_get_user(client):
    # Create user via API
    payload = {"email": "user@example.com", "name": "User Tester"}
    response = client.post("/api/v1/users/", json=payload)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["email"] == "user@example.com"
    assert created_user["name"] == "User Tester"

    # Fetch user via API
    response = client.get(f"/api/v1/users/{created_user['id']}")
    assert response.status_code == 200
    fetched_user = response.json()
    assert fetched_user["email"] == "user@example.com"
    assert fetched_user["name"] == "User Tester"


def test_update_user(client):
    # Create user first
    payload = {"email": "update@example.com", "name": "Update Tester"}
    response = client.post("/api/v1/users/", json=payload)
    user_id = response.json()["id"]

    # Update user name
    response = client.patch(f"/api/v1/users/{user_id}", json={"name": "Updated Name"})
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["name"] == "Updated Name"


def test_delete_user(client):
    # Create user first
    payload = {"email": "delete@example.com", "name": "Delete Tester"}
    response = client.post("/api/v1/users/", json=payload)
    user_id = response.json()["id"]

    # Delete user
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 200

    # Verify deletion
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 404


def test_get_nonexistent_user(client):
    # Try to fetch a user that doesn't exist
    response = client.get("/api/v1/users/9999")
    assert response.status_code == 404

