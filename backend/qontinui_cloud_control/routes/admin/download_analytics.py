"""Admin download analytics endpoints."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin_deps import require_admin
from app.api.deps import get_async_db
from app.models.user import User
from qontinui_cloud_control.repositories.download_analytics import download_analytics_repository

router = APIRouter()


@router.get("/download-analytics")
async def get_download_analytics(
    days: int = 30,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Get runner download analytics.

    Returns aggregated download statistics including:
    - Total downloads and unique downloaders
    - Downloads by country, platform, browser
    - Daily download trends
    - UTM campaign attribution

    Query params:
        - days: Number of days to look back (default 30)
    """
    return await download_analytics_repository.get_download_analytics(db, days=days)
