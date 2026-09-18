# ============================================================
# FASTAPI APPLICATION
# ============================================================
#
# AI Email Copilot Backend
#
# Run:
#   python -m uvicorn backend.api:app --reload
#
# From the EmailAgent directory.
# ============================================================

import sys
import os
import logging

# Add project root to path so modules can be found
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.auth import (
    router as auth_router,
    get_current_user
)
from backend.routes.dashboard import (
    router as dashboard_router
)
from backend.routes.tasks import (
    router as tasks_router
)
from backend.routes.drafts import (
    router as drafts_router
)
from backend.routes.emails import (
    router as emails_router
)
from backend.routes.calendar import (
    router as calendar_router
)
from backend.routes.processing import (
    router as processing_router
)
from backend.routes.agent import (
    router as agent_router
)
from backend.routes.notifications import (
    router as notifications_router
)
from backend.routes.push import (
    router as push_router
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Email Copilot",
    description=(
        "An AI-powered email assistant that reads Gmail, "
        "understands emails, manages tasks, creates "
        "calendar events, and generates reply drafts."
    ),
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# REGISTER ROUTES
# ============================================================

# Auth routes (public — no token required)
app.include_router(auth_router)

# Protected routes (require JWT)
app.include_router(
    dashboard_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    tasks_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    drafts_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    emails_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    calendar_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    processing_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    agent_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    notifications_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    push_router,
    dependencies=[Depends(get_current_user)]
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Email Copilot"
    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("AI Email Copilot backend starting...")

    try:
        from database import ensure_indexes
        ensure_indexes()
        logger.info("Database indexes ensured.")
    except Exception as e:
        logger.warning(
            "Could not ensure indexes: %s", str(e)
        )

    try:
        from backend.user_store import ensure_user_indexes
        ensure_user_indexes()
    except Exception as e:
        logger.warning(
            "Could not ensure user indexes: %s", str(e)
        )

    # Start background email watcher
    try:
        from backend.email_watcher import start_watcher
        await start_watcher()
        logger.info("Email watcher started.")
    except Exception as e:
        logger.warning(
            "Could not start email watcher: %s", str(e)
        )


# ============================================================
# SHUTDOWN
# ============================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("AI Email Copilot backend shutting down...")

    try:
        from backend.email_watcher import stop_watcher
        await stop_watcher()
    except Exception as e:
        logger.warning(
            "Error stopping email watcher: %s", str(e)
        )
