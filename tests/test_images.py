from app.models.user import User
from app.models.image import Image


def test_upload_image(client, db):
    # Seed a user first
    user = User(email="imgtest@example.com", name="Image Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    payload = {
        "user_id": user.id,
        "file_path": "uploads/test.png",
        "image_type": "profile",
        "status": "pending",
        "analysis_result": None,
    }
    response = client.post("/api/v1/images/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["file_path"] == "uploads/test.png"
    assert data["user_id"] == user.id


def test_get_image(client, db):
    # Seed a user and image directly
    user = User(email="imgfetch@example.com", name="Img Fetch Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    image = Image(user_id=user.id, file_path="uploads/fetch.png", image_type="profile", status="pending")
    db.add(image)
    db.commit()
    db.refresh(image)

    response = client.get(f"/api/v1/images/{image.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["file_path"] == "uploads/fetch.png"


def test_delete_image(client, db):
    # Seed a user and image directly
    user = User(email="imgdel@example.com", name="Img Del Tester")
    db.add(user)
    db.commit()
    db.refresh(user)

    image = Image(user_id=user.id, file_path="uploads/delete.png", image_type="profile", status="pending")
    db.add(image)
    db.commit()
    db.refresh(image)

    # Delete image
    response = client.delete(f"/api/v1/images/{image.id}")
    assert response.status_code == 200

    # Verify deletion
    response = client.get(f"/api/v1/images/{image.id}")
    assert response.status_code == 404


def test_get_nonexistent_image(client):
    # Try to fetch an image that doesn't exist
    response = client.get("/api/v1/images/9999")
    assert response.status_code == 404

