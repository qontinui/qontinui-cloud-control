"""qontinui-cloud-control — proprietary cloud-only extension to qontinui-web.

Importing this package side-effect-registers the cloud-control routes,
models, services, and permission checks with the OSS extension surface
(``app.extensions``).

In M1 of the carve-out this file is empty (no registrars). M2 wires the
four ``add_route_registrar`` / ``add_model_registrar`` /
``register_org_permission_check`` / ``register_service`` calls per
``tmp_cloud_control_carve_out.md`` §3.5.
"""
