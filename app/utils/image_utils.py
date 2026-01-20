from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.image import Image
from app.schemas.image import ImageCreate, ImageUpdate
from app.models.image import ImageStatus, ImageType
from app.core.file_validation import validate_file_extension


# --------------------------- # VALIDATION HELPERS # ---------------------------
def validate_image_type(image_type: ImageType):
    """Ensure the provided image_type is valid."""
    if image_type not in ImageType.__members__.values():
        raise HTTPException(status_code=422, detail="Invalid image type")


def validate_image_status(status: ImageStatus):
    """Ensure the provided image status is valid."""
    if status not in ImageStatus.__members__.values():
        raise HTTPException(status_code=422, detail="Invalid image status")


# --------------------------- # CREATE Image Entry # ---------------------------
def create_image_entry(payload: ImageCreate, db: Session) -> Image:
    """
    Create a new image record in the database.
    Supports domain and view metadata (e.g. diet/meal, diet/barcode, skincare/front).
    """
    # Validate file path and extension
    validate_file_extension(payload.file_path)
    
    if payload.image_type:
        validate_image_type(payload.image_type)
    if payload.status:
        validate_image_status(payload.status)

    new_image = Image(
        user_id=payload.user_id,
        file_path=payload.file_path,
        image_type=payload.image_type,
        status=payload.status or ImageStatus.pending,
        analysis_result=payload.analysis_result,
        domain=payload.domain,
        view=payload.view,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


# --------------------------- # GET Image by ID & User # ---------------------------
def get_image_status(user_id: int, image_id: int, db: Session) -> Image:
    """Fetch an image by ID, ensuring it belongs to the given user."""
    image = db.query(Image).filter(Image.id == image_id, Image.user_id == user_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found or unauthorized")
    return image


# --------------------------- # MARK Image Processed # ---------------------------
def mark_image_processed(image_id: int, analysis_result, db: Session) -> Image:
    """Mark an image as processed and attach analysis results."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.status = ImageStatus.processed
    image.analysis_result = analysis_result
    image.processed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(image)
    return image


# --------------------------- # MARK Image Failed # ---------------------------
def mark_image_failed(image_id: int, db: Session) -> Image:
    """Mark an image as failed."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.status = ImageStatus.failed
    image.processed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(image)
    return image


# --------------------------- # UPDATE Image Entry # ---------------------------
def update_image_entry(image_id: int, payload: ImageUpdate, db: Session) -> Image:
    """
    Update an existing image record.
    Allows updating analysis_result, status, image_type, domain, and view.
    """
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if payload.status == ImageStatus.processed and payload.analysis_result is not None:
        return mark_image_processed(image_id, payload.analysis_result, db)
    elif payload.status == ImageStatus.failed:
        return mark_image_failed(image_id, db)

    if payload.analysis_result is not None:
        image.analysis_result = payload.analysis_result
    if payload.status is not None:
        validate_image_status(payload.status)
        image.status = payload.status
    if payload.image_type is not None:
        validate_image_type(payload.image_type)
        image.image_type = payload.image_type
    if payload.domain is not None:
        image.domain = payload.domain
    if payload.view is not None:
        image.view = payload.view

    image.processed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(image)
    return image


# --------------------------- # DELETE Image Entry # ---------------------------
def delete_image_record(image_id: int, db: Session):
    """Delete an image record by ID."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    db.delete(image)
    db.commit()
    return {"status": "deleted", "image_id": image_id}

