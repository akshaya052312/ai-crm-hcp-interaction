"""
Pydantic Schemas — Request / Response Models

Defines all request bodies, response envelopes, and data models
used by the FastAPI routes. Ensures strict validation at the API boundary.
"""

from datetime import date, time, datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# Generic API Response Envelope
# ═══════════════════════════════════════════════════════════════

class APIResponse(BaseModel):
    """Standard response wrapper used by every endpoint."""
    success: bool
    data: Any = None
    message: str = ""


# ═══════════════════════════════════════════════════════════════
# Interaction Schemas
# ═══════════════════════════════════════════════════════════════

class LogInteractionRequest(BaseModel):
    """POST /api/interactions/log — free-text note from the field rep."""
    note: str = Field(
        ...,
        min_length=5,
        description="Natural language note describing the HCP interaction",
        json_schema_extra={"example": "Met Dr. Smith today, discussed Product X efficacy, positive sentiment, shared brochure"},
    )


class EditInteractionRequest(BaseModel):
    """PUT /api/interactions/{id} — natural language edit instruction."""
    edit_request: str = Field(
        ...,
        min_length=3,
        description="Natural language description of the change",
        json_schema_extra={"example": "Change sentiment to positive and update outcomes to 'Agreed to trial'"},
    )



class SuggestFollowUpResponse(BaseModel):
    """Nested data returned by the suggest-followup endpoint."""
    interaction_id: str
    suggestions: list[str]
    count: int


# ═══════════════════════════════════════════════════════════════
# HCP Schemas
# ═══════════════════════════════════════════════════════════════

class HCPOut(BaseModel):
    """Serialised HCP record returned by search and list endpoints."""
    id: str
    name: str
    specialty: str
    location: Optional[str] = None
    hospital: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Interaction Detail Schema (for history / get responses)
# ═══════════════════════════════════════════════════════════════

class InteractionOut(BaseModel):
    """Serialised interaction record."""
    id: str
    hcp_id: str
    interaction_type: str
    date: date
    time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MaterialOut(BaseModel):
    """Serialised material shared record."""
    id: str
    material_name: str
    material_type: str

    model_config = {"from_attributes": True}


class SampleOut(BaseModel):
    """Serialised sample distributed record."""
    id: str
    sample_name: str
    quantity: int

    model_config = {"from_attributes": True}


class FollowUpOut(BaseModel):
    """Serialised follow-up suggestion record."""
    id: str
    suggestion_text: str
    generated_by_ai: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Chat Schema
# ═══════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """POST /api/chat — free-text message to the LangGraph agent."""
    message: str = Field(
        ...,
        min_length=1,
        description="User message to send to the CRM agent",
        json_schema_extra={"example": "Show me all interactions with Dr. Patel"},
    )


class ChatResponse(BaseModel):
    """Agent response from the chat endpoint."""
    reply: str
    tool_calls: list[str] = Field(
        default_factory=list,
        description="Names of tools invoked during this turn",
    )
