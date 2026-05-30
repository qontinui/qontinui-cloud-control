"""qontinui-cloud-control — proprietary cloud-only extension to qontinui-web.

Importing this package side-effect-registers the cloud-control routes,
models, services, and permission checks with the OSS extension surface.
"""
from app.extensions import (
    add_model_registrar,
    add_route_registrar,
    register_service,
)


def _register_routes(api_router):
    from qontinui_cloud_control.routes import (
        admin_ws,
        billing,
        organizations,
    )
    from qontinui_cloud_control.routes import admin as admin_pkg

    api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
    api_router.include_router(admin_pkg.router, prefix="/admin", tags=["admin"])
    api_router.include_router(admin_ws.router, prefix="/admin", tags=["admin-websockets"])
    api_router.include_router(
        organizations.router, prefix="/organizations", tags=["organizations"]
    )


def _register_models():
    # Side-effect: importing the model modules adds them to SQLAlchemy's Base.metadata
    from qontinui_cloud_control.models import (  # noqa: F401
        admin_notification_settings,
        subscription,
    )


def _register_services():
    # Reserve the service slot pattern for follow-up wiring (auth_analytics
    # aggregator, billing service singleton). Empty in M2; populated as
    # cross-package call sites need it.
    pass


add_route_registrar(_register_routes)
add_model_registrar(_register_models)
_register_services()
