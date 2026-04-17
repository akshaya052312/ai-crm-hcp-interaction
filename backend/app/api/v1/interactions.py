"""
Interaction Routes — /api/interactions

Endpoints:
  POST /log                       — Log a new interaction via LLM extraction
  PUT  /{id}                      — Edit an existing interaction via LLM
  GET  /hcp/{hcp_id}              — Get HCP interaction history (LLM summary)
  POST /{id}/suggest-followup     — Generate AI follow-up suggestions
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.agents.tools import (
    log_interaction,
    edit_interaction,
    get_hcp_history,
    suggest_follow_up,
)
from app.models.schemas import (
    APIResponse,
    LogInteractionRequest,
    EditInteractionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/interactions",
    tags=["Interactions"],
)


# ─────────────────────────────────────────────────────────────
# POST /api/interactions/log
# ─────────────────────────────────────────────────────────────

@router.post("/log", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def api_log_interaction(body: LogInteractionRequest):
    """Log a new HCP interaction from a natural-language note.

    The note is parsed by the LLM to extract structured entities
    (HCP name, topics, sentiment, materials, samples, etc.) and
    saved to the database.
    """
    try:
        result = log_interaction.invoke({"note": body.note})

        # Check for tool-level errors (returned as string starting with ❌)
        if result.startswith("❌"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result,
            )

        return APIResponse(success=True, data=result, message="Interaction logged successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to log interaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────
# PUT /api/interactions/{id}
# ─────────────────────────────────────────────────────────────

@router.put("/{interaction_id}", response_model=APIResponse)
async def api_edit_interaction(interaction_id: str, body: EditInteractionRequest):
    """Edit an existing interaction using a natural-language change request.

    The LLM interprets the edit instruction, maps it to database fields,
    and applies the update.
    """
    # Validate UUID format
    try:
        UUID(interaction_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interaction ID format: {interaction_id}",
        )

    try:
        result = edit_interaction.invoke({
            "interaction_id": interaction_id,
            "edit_request": body.edit_request,
        })

        if "not found" in result.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result,
            )

        if result.startswith("❌"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result,
            )

        return APIResponse(success=True, data=result, message="Interaction updated")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to edit interaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────
# GET /api/interactions/hcp/{hcp_id}
# ─────────────────────────────────────────────────────────────

@router.get("/hcp/{hcp_id}", response_model=APIResponse)
async def api_get_hcp_history(hcp_id: str, limit: int = 10):
    """Retrieve and summarise the interaction history for a specific HCP.

    Accepts either a UUID or a name (partial match). The history
    is summarised by the LLM.
    """
    try:
        result = get_hcp_history.invoke({
            "hcp_identifier": hcp_id,
            "limit": limit,
        })

        if "No HCP found" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result,
            )

        return APIResponse(success=True, data=result, message="History retrieved")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get HCP history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────
# POST /api/interactions/{id}/suggest-followup
# ─────────────────────────────────────────────────────────────

@router.post("/{interaction_id}/suggest-followup", response_model=APIResponse)
async def api_suggest_follow_up(interaction_id: str):
    """Generate AI-powered follow-up suggestions for a specific interaction.

    The LLM analyses the interaction context to produce 2-3 actionable
    follow-up items which are saved to the database.
    """
    # Validate UUID format
    try:
        UUID(interaction_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interaction ID format: {interaction_id}",
        )

    try:
        result = suggest_follow_up.invoke({
            "interaction_id": interaction_id,
        })

        if "not found" in result.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result,
            )

        if result.startswith("❌"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result,
            )

        return APIResponse(success=True, data=result, message="Follow-up suggestions generated")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate follow-up suggestions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}",
        )

