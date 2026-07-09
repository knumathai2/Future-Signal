"""Category route for currently servable issues.

When live DB data is available, categories must come from the same live issue
set that `/api/issues` serves so filter buttons cannot point at empty exact
matches. The static sample list remains the DB-free/local fallback.
"""
import logging
from collections.abc import Generator

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.category_taxonomy import issue_category_labels, sort_category_labels
from app.core.config import settings
from app.db.queries import load_live_issues
from app.db.session import get_db
from app.schemas.issues import CategoryListResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["categories"])

_SAMPLE_CATEGORIES = ["환경", "경제"]


def _get_optional_db() -> Generator[Session | None, None, None]:
    if not settings.database_url:
        yield None
        return
    yield from get_db()


@router.get("/api/categories", response_model=CategoryListResponse)
def list_categories(
    db: Session | None = Depends(_get_optional_db),
) -> CategoryListResponse:
    if db is not None:
        try:
            live = load_live_issues(db)
        except SQLAlchemyError:
            logger.warning(
                "FALLBACK: live category query failed, serving sample categories.",
                exc_info=True,
            )
        else:
            if live is not None:
                live_issues, _ = live
                categories = sort_category_labels(
                    {
                        label
                        for li in live_issues
                        for label in issue_category_labels(li.market.title, li.market.category)
                    }
                )
                return CategoryListResponse(categories=categories)

    return CategoryListResponse(categories=_SAMPLE_CATEGORIES)
