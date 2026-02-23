"""
Domain routes.
Handles domain-specific questionnaire flows, AI processing,
and diet-specific food scanning features.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.ai.diet.food_scanner import analyze_food_image
from app.core.config import settings
from app.core.database import get_async_db
from app.core.file_validation import validate_upload_file
from app.core.logging import logger
from app.core.rate_limit import RateLimits, limiter
from app.models.image import ImageType
from app.models.user import User
from app.schemas.domain import (
    DomainAnswerCreate,
    DomainAnswersOut,
    DomainFlowOut,
    DomainProgressOut,
    DomainQuestionOut,
    AllDomainsProgressOut,
    FoodAnalysisOut,
    BarcodeProductOut,
)
from app.services.domain_service import DomainService
from app.services.image_service import ImageService
from app.utils.jwt_utils import get_current_user

router = APIRouter()


# ── Diet Specific Endpoints ───────────────────────────────────────
# MUST be before /{domain}/... routes to avoid FastAPI route conflicts

@router.post("/diet/foods/analyze", response_model=FoodAnalysisOut)
@limiter.limit(RateLimits.UPLOAD)
async def analyze_food(
    request: Request,  # noqa: ARG001
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze food image using Gemini AI vision.

    Upload an image of food to get:
    - Food identification
    - Nutrition information (calories, protein, carbs, fat)
    - Health insights and recommendations
    """
    await validate_upload_file(file)

    image_service = ImageService(db)
    image = await image_service.upload_image(
        file=file,
        user_id=current_user.id,
        domain="diet",
        view="meal",
        image_type=ImageType.uploaded
    )

    image_url = image_service.get_image_url(image)
    result = analyze_food_image(image_url)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not analyze food image. Please try with a clearer photo."
        )

    logger.info(
        f"Food analyzed for user {current_user.id}: "
        f"{result.get('food_name')} - "
        f"{result.get('nutrition', {}).get('calories')} kcal"
    )

    return {"image_id": image.id, "image_url": image_url, **result}


@router.get("/diet/foods/barcode/{barcode}", response_model=BarcodeProductOut)
@limiter.limit(RateLimits.BARCODE)
async def get_barcode_info(
    request: Request,  # noqa: ARG001
    barcode: str,
    current_user: User = Depends(get_current_user),  # noqa: ARG001
):
    """
    Get food product nutrition info from barcode using Open Food Facts database.

    Supports international barcodes (EAN, UPC).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        data = response.json()
        if data.get("status") != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found in barcode database"
            )

        product = data.get("product", {})
        nutrients = product.get("nutriments", {})

        logger.info(f"Barcode {barcode} looked up for user {current_user.id}")

        return {
            "barcode": barcode,
            "food_name": product.get("product_name", "Unknown Product"),
            "brand": product.get("brands", ""),
            "portion_size": product.get("serving_size", "100g"),
            "nutrition": {
                "calories": round(nutrients.get("energy-kcal_100g", 0), 1),
                "protein": round(nutrients.get("proteins_100g", 0), 1),
                "carbs": round(nutrients.get("carbohydrates_100g", 0), 1),
                "fat": round(nutrients.get("fat_100g", 0), 1),
                "fiber": round(nutrients.get("fiber_100g", 0), 1),
                "sugar": round(nutrients.get("sugars_100g", 0), 1),
            },
            "image_url": product.get("image_url"),
            "tip": "Nutrition values are per 100g unless portion size is specified."
        }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Barcode lookup timed out. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Barcode lookup error for {barcode}: {e}",
            exc_info=settings.is_development
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lookup barcode"
        )


# ── Progress Overview ─────────────────────────────────────────────

@router.get("/progress/overview", response_model=AllDomainsProgressOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_all_domains_progress(
    request: Request,  # noqa: ARG001
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get progress overview across all domains for Home screen chart.

    Returns progress percentage for each domain:
    - Skincare
    - Haircare
    - Workout
    - Diet
    - Fashion
    - Height
    - Facial
    - Quit Porn
    """
    domain_service = DomainService(db)
    return await domain_service.get_all_domains_progress(current_user.id)


# ── Generic Domain Routes ─────────────────────────────────────────
# These routes work for ALL domains (skincare, haircare, workout, diet, etc.)

@router.get("/{domain}/questions", response_model=list[DomainQuestionOut])
@limiter.limit(RateLimits.DEFAULT)
async def get_domain_questions(
    request: Request,  # noqa: ARG001
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),  # noqa: ARG001
):
    """
    Get all questions for a specific domain.

    **Valid domains:**
    - skincare, haircare, workout, diet, fashion, height, facial, quit_porn
    """
    domain_service = DomainService(db)
    domain_service.validate_domain(domain)
    return await domain_service.get_domain_questions(domain)


@router.get("/{domain}/flow", response_model=DomainFlowOut)
@limiter.limit(RateLimits.AI)
async def get_domain_flow(
    request: Request,  # noqa: ARG001
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current domain flow state (next question or AI completion status).

    Returns either:
    - Next question to answer
    - AI processing status
    - Completion status with redirect
    """
    domain_service = DomainService(db)
    domain_service.validate_domain(domain)
    await domain_service.check_domain_access(current_user.id, domain)
    return await domain_service.next_or_complete(current_user.id, domain)


@router.post("/{domain}/answers", response_model=DomainFlowOut)
@limiter.limit(RateLimits.DEFAULT)
async def submit_domain_answer(
    request: Request,  # noqa: ARG001
    domain: str,
    payload: DomainAnswerCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit an answer to a domain question.

    After submitting, returns the next question or completion status.
    """
    domain_service = DomainService(db)
    payload.user_id = current_user.id
    domain_service.validate_domain(domain)
    await domain_service.check_domain_access(current_user.id, domain)
    await domain_service.save_answer(domain, payload)
    return await domain_service.next_or_complete(current_user.id, domain)


@router.get("/{domain}/progress", response_model=DomainProgressOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_domain_progress(
    request: Request,  # noqa: ARG001
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get progress for a specific domain.

    Returns:
    - Total questions
    - Answered questions
    - Completion percentage
    - AI processing status
    """
    domain_service = DomainService(db)
    domain_service.validate_domain(domain)
    return await domain_service.calculate_progress(domain, current_user.id)


@router.get("/{domain}/answers", response_model=DomainAnswersOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_domain_answers(
    request: Request,  # noqa: ARG001
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all user's answers for a specific domain.

    Returns answers with question context.
    """
    domain_service = DomainService(db)
    domain_service.validate_domain(domain)
    answers = await domain_service.get_user_answers(domain, current_user.id)
    return {
        "user_id": current_user.id,
        "domain": domain,
        "answers": answers
    }


@router.post("/{domain}/retry-ai", response_model=DomainFlowOut)
@limiter.limit(RateLimits.AI)
async def retry_ai_processing(
    request: Request,  # noqa: ARG001
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retry AI processing for a domain if it failed.

    Useful when AI processing times out or encounters an error.
    """
    domain_service = DomainService(db)
    domain_service.validate_domain(domain)
    await domain_service.check_domain_access(current_user.id, domain)
    return await domain_service.next_or_complete(current_user.id, domain)


@router.get("/{domain}/access")
@limiter.limit(RateLimits.DEFAULT)
async def check_domain_access(
    request: Request,  # noqa: ARG001
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if user has access to a specific domain.

    Access is granted based on:
    - User's selected domain during onboarding
    - Active subscription status
    """
    domain_service = DomainService(db)
    try:
        domain_service.validate_domain(domain)
        await domain_service.check_domain_access(current_user.id, domain)
        return {
            "has_access": True,
            "domain": domain,
            "user_id": current_user.id,
            "message": "Access granted"
        }
    except HTTPException as e:
        return {
            "has_access": False,
            "domain": domain,
            "user_id": current_user.id,
            "message": e.detail
        }

