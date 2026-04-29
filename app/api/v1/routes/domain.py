import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

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
    DomainBulkAnswerCreate,
    DomainAnswersOut,
    DomainFlowOut,
    DomainQuestionOut,
    AllDomainsProgressOut,
    FoodAnalysisOut,
    BarcodeProductOut,
)
from app.services.domain_service import DomainService
from app.services.progress_service import ProgressService
from app.services.image_service import ImageService
from app.utils.domain_utils import validate_domain
from app.utils.jwt_utils import get_current_user

router = APIRouter()

# Define before use
_EXPLORE_DOMAINS = [
    {"key": "skincare",  "name": "Skincare",   "subtitle": "Daily glow routine",    "icon_url": "https://api.lookslabai.com/static/icons/SkinCare.jpg"},
    {"key": "haircare",  "name": "Hair",        "subtitle": "Boost hair health",     "icon_url": "https://api.lookslabai.com/static/icons/Hair.png"},
    {"key": "workout",   "name": "Workout",     "subtitle": "Build strength daily",  "icon_url": "https://api.lookslabai.com/static/icons/Workout.jpg"},
    {"key": "diet",      "name": "Diet",        "subtitle": "Eat smart, feel great", "icon_url": "https://api.lookslabai.com/static/icons/Diet.jpg"},
    {"key": "facial",    "name": "Facial",      "subtitle": "Define your features",  "icon_url": "https://api.lookslabai.com/static/icons/Facial.jpg"},
    {"key": "fashion",   "name": "Fashion",     "subtitle": "Own your style",        "icon_url": "https://api.lookslabai.com/static/icons/Fashion.png"},
    {"key": "height",    "name": "Height",      "subtitle": "Improve your posture",  "icon_url": "https://api.lookslabai.com/static/icons/Height.jpg"},
    {"key": "quit_porn", "name": "Quit Porn",   "subtitle": "Reclaim your focus",    "icon_url": "https://api.lookslabai.com/static/icons/QuitPorn.jpg"},
]


@router.post("/diet/foods/analyze", response_model=FoodAnalysisOut)
@limiter.limit(RateLimits.UPLOAD)
async def analyze_food(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    detected_mime_type = await validate_upload_file(file)
    image_service = ImageService(db)
    image = await image_service.upload_image(
        file=file, user_id=current_user.id, domain="diet",
        view="meal", image_type=ImageType.uploaded,
        detected_mime_type=detected_mime_type,
    )
    image_url = image_service.get_image_url(image)
    result = analyze_food_image(image_url)
    if not result:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Could not analyze food image. Please try with a clearer photo.")
    logger.info(f"Food analyzed for user {current_user.id}: {result.get('food_name')} - {result.get('nutrition', {}).get('calories')} kcal")
    return {"image_id": image.id, "image_url": image_url, **result}


@router.get("/diet/foods/barcode/{barcode}", response_model=BarcodeProductOut)
@limiter.limit(RateLimits.BARCODE)
async def get_barcode_info(
    request: Request,
    barcode: str,
    current_user: User = Depends(get_current_user),
):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json")
        if response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        data = response.json()
        if data.get("status") != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in barcode database")
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
                "protein":  round(nutrients.get("proteins_100g", 0), 1),
                "carbs":    round(nutrients.get("carbohydrates_100g", 0), 1),
                "fat":      round(nutrients.get("fat_100g", 0), 1),
                "fiber":    round(nutrients.get("fiber_100g", 0), 1),
                "sugar":    round(nutrients.get("sugars_100g", 0), 1),
            },
            "image_url": product.get("image_url"),
            "tip": "Nutrition values are per 100g unless portion size is specified."
        }
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Barcode lookup timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Barcode lookup error for {barcode}: {e}", exc_info=settings.is_development)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to lookup barcode")


@router.get("/progress/overview", response_model=AllDomainsProgressOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_all_domains_progress(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    return await DomainService(db).get_all_domains_progress(current_user.id)


@router.get("/explore")
@limiter.limit(RateLimits.DEFAULT)
async def get_explore_domains(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return {"domains": _EXPLORE_DOMAINS}


@router.get("/{domain}/progress/graph")
@limiter.limit(RateLimits.DEFAULT)
async def get_domain_progress_graph(
    request: Request,
    domain: str,
    period: str = Query("weekly", pattern="^(weekly|monthly|yearly)$"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get progress graph for a specific domain. period: weekly | monthly | yearly"""
    validate_domain(domain)
    return await ProgressService(db).get_domain_progress_graph(current_user.id, domain, period)


@router.get("/{domain}/questions", response_model=list[DomainQuestionOut])
@limiter.limit(RateLimits.DEFAULT)
async def get_domain_questions(
    request: Request,
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainService(db)
    validate_domain(domain)
    return await service.get_domain_questions(domain)


@router.get("/{domain}/flow", response_model=DomainFlowOut, response_model_exclude_none=True)
@limiter.limit(RateLimits.AI)
async def get_domain_flow(
    request: Request,
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainService(db)
    validate_domain(domain)
    await service.check_domain_access(current_user.id, domain)
    return await service.next_or_complete(current_user.id, domain)


@router.post("/{domain}/answers", response_model=DomainFlowOut, response_model_exclude_none=True)
@limiter.limit(RateLimits.DEFAULT)
async def submit_domain_answer(
    request: Request,
    domain: str,
    payload: DomainAnswerCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainService(db)
    payload.user_id = current_user.id
    validate_domain(domain)
    await service.check_domain_access(current_user.id, domain)
    await service.save_answer(domain, payload)
    return await service.next_or_complete(current_user.id, domain)


@router.post("/{domain}/answers/bulk", response_model=DomainFlowOut)
@limiter.limit(RateLimits.DEFAULT)
async def submit_domain_answers_bulk(
    request: Request,
    domain: str,
    payload: DomainBulkAnswerCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    import hashlib, json as _json

    service = DomainService(db)
    validate_domain(domain)
    await service.check_domain_access(current_user.id, domain)

    # Compute stable hash of this submission (sorted for consistency)
    payload_hash = hashlib.sha256(
        _json.dumps(
            sorted([(a.question_id, str(a.answer)) for a in payload.answers])
        ).encode()
    ).hexdigest()[:16]

    # Check if same payload was already submitted and AI is running/completed
    cached_hash = await service.get_submission_hash(current_user.id, domain)
    existing_task = await service.get_cached_ai_task(current_user.id, domain)

    if cached_hash == payload_hash and existing_task:
        if existing_task["status"] == "completed" and existing_task["result"] is not None:
            logger.info(f"Duplicate bulk submission for {domain} (user {current_user.id}) — returning cached result")
            return existing_task["result"]
        elif existing_task["status"] == "processing":
            logger.info(f"Duplicate bulk submission for {domain} (user {current_user.id}) — AI still processing")
            progress = await service.calculate_progress(domain, current_user.id)
            return DomainFlowOut(
                status="processing",
                current=None,
                next=None,
                progress=progress,
                redirect="processing",
            )

    # Save answers (upsert — safe to run multiple times)
    for answer in payload.answers:
        answer.user_id = current_user.id
        answer.domain = domain
        await service.save_answer(domain, answer)

    # Store hash so duplicate retries are caught
    await service.remember_submission_hash(current_user.id, domain, payload_hash)

    return await service.next_or_complete(current_user.id, domain, submission_hash=payload_hash)


@router.get("/{domain}/answers", response_model=DomainAnswersOut)
@limiter.limit(RateLimits.DEFAULT)
async def get_domain_answers(
    request: Request,
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainService(db)
    validate_domain(domain)
    answers = await service.get_user_answers(domain, current_user.id)
    return {"user_id": current_user.id, "domain": domain, "answers": answers}


@router.delete("/{domain}/answers")
@limiter.limit(RateLimits.DEFAULT)
async def reset_domain_answers(
    request: Request,
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainService(db)
    validate_domain(domain)
    await service.reset_domain_answers(current_user.id, domain)
    return {"message": f"Answers for domain '{domain}' have been reset. You can now retake the flow."}


@router.post("/{domain}/retry-ai", response_model=DomainFlowOut, response_model_exclude_none=True)
@limiter.limit(RateLimits.AI)
async def retry_ai_processing(
    request: Request,
    domain: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    service = DomainService(db)
    validate_domain(domain)
    await service.check_domain_access(current_user.id, domain)
    return await service.next_or_complete(current_user.id, domain)

