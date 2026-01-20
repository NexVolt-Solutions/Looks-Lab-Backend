from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.image import ImageCreate, ImageUpdate, ImageOut
from app.utils.jwt_utils import get_current_user
from app.utils.image_utils import (
    create_image_entry,
    get_image_status,
    update_image_entry,
    delete_image_record,
)

router = APIRouter(tags=["Images"])


# --------------------------- # POST Upload Image # ---------------------------
@router.post("/", response_model=ImageOut)
def upload_image(
    payload: ImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Register a new image record (uploaded or generated) for the authenticated user.
    Supports domain and view metadata (e.g. diet/meal, diet/barcode, skincare/front).
    """
    payload.user_id = current_user.id
    return create_image_entry(payload, db)


# --------------------------- # POST Scan Food (Diet) # ---------------------------
@router.post("/diet/scan-food", response_model=ImageOut)
def scan_food(
    payload: ImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a food image (meal photo) for diet tracking."""
    payload.user_id = current_user.id
    payload.domain = "diet"
    payload.view = "meal"
    return create_image_entry(payload, db)


# --------------------------- # POST Scan Barcode (Diet) # ---------------------------
@router.post("/diet/scan-barcode", response_model=ImageOut)
def scan_barcode(
    payload: ImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a barcode image for diet tracking."""
    payload.user_id = current_user.id
    payload.domain = "diet"
    payload.view = "barcode"
    return create_image_entry(payload, db)


# --------------------------- # POST Upload Gallery Image (Diet) # ---------------------------
@router.post("/diet/gallery", response_model=ImageOut)
def upload_gallery_image(
    payload: ImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a gallery image for diet tracking."""
    payload.user_id = current_user.id
    payload.domain = "diet"
    payload.view = "gallery"
    return create_image_entry(payload, db)


# --------------------------- # GET Image by ID # ---------------------------
@router.get("/{image_id}", response_model=ImageOut)
def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a single image by ID, only if it belongs to the authenticated user."""
    image = get_image_status(current_user.id, image_id, db)
    if not image or image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this image")
    return image


# --------------------------- # PATCH Update Image # ---------------------------
@router.patch("/{image_id}", response_model=ImageOut)
def update_image(
    image_id: int,
    payload: ImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update analysis result, domain, view, or status for an image if it belongs to the authenticated user."""
    image = get_image_status(current_user.id, image_id, db)
    if not image or image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this image")
    return update_image_entry(image_id, payload, db)


# --------------------------- # DELETE Image # ---------------------------
@router.delete("/{image_id}")
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an image record if it belongs to the authenticated user."""
    image = get_image_status(current_user.id, image_id, db)
    if not image or image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this image")
    return delete_image_record(image_id, db)

