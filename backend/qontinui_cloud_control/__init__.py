"""qontinui-cloud-control — cloud extension to qontinui-web (AGPL-3.0-or-later).

Importing this package side-effect-registers the cloud-control routes,
models, services, and permission checks with the OSS extension surface.
"""

from app.extensions import (
    add_model_registrar,
    add_route_registrar,
)


def _register_routes(api_router):
    from qontinui_cloud_control.routes import admin as admin_pkg
    from qontinui_cloud_control.routes import (
        admin_ws,
        billing,
        organizations,
    )

    api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
    api_router.include_router(admin_pkg.router, prefix="/admin", tags=["admin"])
    api_router.include_router(
        admin_ws.router, prefix="/admin", tags=["admin-websockets"]
    )
    api_router.include_router(
        organizations.router, prefix="/organizations", tags=["organizations"]
    )


def _register_models():
    # Side-effect: importing the model modules adds them to SQLAlchemy's Base.metadata
    from qontinui_cloud_control.models import (  # noqa: F401
        admin_notification_settings,
        subscription,
    )


add_route_registrar(_register_routes)
add_model_registrar(_register_models)

# No `register_service()` call: the `app.extensions` service-slot mechanism
# exists for OSS code that reaches INTO cloud-control via `get_service(name)`,
# and no such OSS call site exists. cloud-control's own consumers import their
# services directly — `auth_analytics_aggregator`, for instance, is imported by
# `routes/admin/analytics.py`. Wire a slot here when an OSS `get_service()`
# caller actually appears, not before.
