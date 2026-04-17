"""
HCP Routes — /api/hcps

Endpoints:
  GET /search?q=<query>  — Search HCPs by name or specialty
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.agents.tools import search_hcp
from app.models.schemas import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hcps",
    tags=["HCPs"],
)


# ─────────────────────────────────────────────────────────────
# GET /api/hcps/search?q=name
# ─────────────────────────────────────────────────────────────

@router.get("/search", response_model=APIResponse)
async def api_search_hcp(
    q: str = Query(
        ...,
        min_length=1,
        description="Partial name or specialty to search for",
        examples=["Smith", "Cardiology"],
    ),
):
    """Search Healthcare Professionals by name or specialty.

    Performs a case-insensitive partial match against the HCP database.
    Returns up to 20 matching records.
    """
    try:
        result = search_hcp.invoke({"query": q})

        return APIResponse(
            success=True,
            data=result,
            message=f"Search completed for '{q}'",
        )

    except Exception as e:
        logger.exception("Failed to search HCPs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )
