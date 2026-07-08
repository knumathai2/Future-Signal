"""DRAFT: hardcoded sample categories, pending TASK-002 schema + real data."""
from fastapi import APIRouter

from app.schemas.issues import CategoryListResponse

router = APIRouter(tags=["categories"])

_SAMPLE_CATEGORIES = ["politics", "economy", "environment", "technology", "world"]


@router.get("/api/categories", response_model=CategoryListResponse)
def list_categories() -> CategoryListResponse:
    return CategoryListResponse(categories=_SAMPLE_CATEGORIES)
