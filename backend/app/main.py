"""
FastAPI Application Entry Point

Configures:
  - CORS middleware (accepts frontend origin)
  - API router registration (/api/*)
  - Startup event for database table creation
  - Health check endpoint
  - Global exception handler
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.db.database import init_db, engine
from app.models.schemas import APIResponse

# ── Load environment variables ──────────────────────────────
load_dotenv()

# ── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Lifespan — Startup & Shutdown
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on application startup and shutdown.

    Startup:
      1. Tests the database connection
      2. Creates tables if they don't exist (dev convenience)

    Shutdown:
      1. Disposes the SQLAlchemy engine connection pool
    """
    # ── Startup ──
    logger.info("🚀 Starting AI-CRM Backend...")

    try:
        # Verify DB connectivity
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified")
    except Exception as e:
        logger.warning(f"⚠️  Database connection failed: {e}")
        logger.warning("   Tables will be created when the DB becomes available.")

    # Create tables (no-op if they already exist)
    try:
        init_db()
        logger.info("✅ Database tables ready")
    except Exception as e:
        logger.warning(f"⚠️  Could not create tables: {e}")

    logger.info("✅ AI-CRM Backend is ready!")
    logger.info(f"   LLM Model: {os.getenv('LLM_MODEL', 'gemma2-9b-it')}")
    logger.info(f"   Frontend URL: {os.getenv('FRONTEND_URL', 'http://localhost:5173')}")

    yield  # ← Application runs here

    # ── Shutdown ──
    logger.info("🛑 Shutting down AI-CRM Backend...")
    engine.dispose()
    logger.info("✅ Database connections closed")


# ═══════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="AI-CRM — HCP Interaction Logger",
    description=(
        "Backend API for pharma field reps to log, search, and analyse "
        "interactions with Healthcare Professionals. Powered by LangGraph "
        "AI agents and Groq LLM inference."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ═══════════════════════════════════════════════════════════════
# CORS Middleware
# ═══════════════════════════════════════════════════════════════

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# Router Registration
# ═══════════════════════════════════════════════════════════════

app.include_router(api_router)


# ═══════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint — verifies the server is running."""
    return APIResponse(
        success=True,
        data={"status": "healthy"},
        message="AI-CRM backend is running",
    )


# ═══════════════════════════════════════════════════════════════
# Global Exception Handler
# ═══════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler to ensure every error returns consistent JSON."""
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            data=None,
            message=f"Internal server error: {str(exc)}",
        ).model_dump(),
    )
