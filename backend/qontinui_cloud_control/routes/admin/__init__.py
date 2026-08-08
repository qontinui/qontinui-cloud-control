"""
Admin endpoints package.

Provides admin-only endpoints for platform management:
- User management
- Project management
- Analytics and statistics
- Health monitoring
- Download analytics
- Notification settings
- Cleanup operations
"""

# Import sub-routers
from fastapi import APIRouter

from qontinui_cloud_control.routes.admin.analytics import router as analytics_router
from qontinui_cloud_control.routes.admin.cleanup import router as cleanup_router
from qontinui_cloud_control.routes.admin.download_analytics import (
    router as download_analytics_router,
)
from qontinui_cloud_control.routes.admin.health import router as health_router
from qontinui_cloud_control.routes.admin.notifications import (
    router as notifications_router,
)
from qontinui_cloud_control.routes.admin.projects import router as projects_router
from qontinui_cloud_control.routes.admin.users import router as users_router

# Main admin router
router = APIRouter()

# Include all sub-routers
router.include_router(users_router, tags=["admin-users"])
router.include_router(projects_router, tags=["admin-projects"])
router.include_router(analytics_router, tags=["admin-analytics"])
router.include_router(health_router, tags=["admin-health"])
router.include_router(download_analytics_router, tags=["admin-downloads"])
router.include_router(notifications_router, tags=["admin-notifications"])
router.include_router(cleanup_router, tags=["admin-cleanup"])

__all__ = ["router"]
