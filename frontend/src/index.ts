/**
 * qontinui-cloud-control — proprietary cloud-only frontend extension.
 *
 * Importing this package side-effect-registers cloud-control routes,
 * components, services, and contexts with the OSS extension surface
 * (`@qontinui/web/lib/extension-slots`).
 *
 * In M1 of the carve-out this file is empty (no slot registrations). M2
 * wires the registerCloudExtensions({ appRoutes, marketingRoutes,
 * navItems, profilePanels, services }) call per
 * tmp_cloud_control_carve_out.md §4.4.
 */
export {};
