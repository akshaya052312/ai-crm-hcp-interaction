"""
API v1 Router — Aggregates all route groups under /api prefix.

Route groups:
  /api/interactions  — Interaction logging, editing, history, follow-ups
  /api/hcps          — HCP search
  /api/chat          — Free-text LangGraph agent chat
"""

from fastapi import APIRouter

from app.api.v1.interactions import router as interactions_router
from app.api.v1.hcps import router as hcps_router
from app.api.v1.chat import router as chat_router

# Master router — all v1 routes are mounted here
api_router = APIRouter(prefix="/api")

api_router.include_router(interactions_router)
api_router.include_router(hcps_router)
api_router.include_router(chat_router)
