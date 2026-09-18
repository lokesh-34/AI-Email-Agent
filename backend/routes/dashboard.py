# ============================================================
# DASHBOARD ROUTES
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException
from backend.models import DashboardStats
from database import get_dashboard_stats

router = APIRouter()


@router.get(
    "/api/dashboard",
    response_model=DashboardStats
)
async def get_dashboard():
    """Get dashboard statistics."""

    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )
