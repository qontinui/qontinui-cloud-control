/**
 * qontinui-cloud-control — proprietary cloud-only frontend extension.
 *
 * Importing this package side-effect-registers cloud-control routes,
 * components, services, and contexts with the OSS extension surface
 * (`@qontinui/web/lib/extension-slots`).
 */

import { lazy } from "react";
import { registerCloudExtensions } from "@qontinui/web/lib/extension-slots";

registerCloudExtensions({
  appRoutes: [
    {
      path: "/billing/success",
      Component: lazy(() => import("./routes/billing/success")),
    },
    {
      path: "/billing/canceled",
      Component: lazy(() => import("./routes/billing/canceled")),
    },
    {
      path: "/pricing",
      Component: lazy(() => import("./routes/pricing")),
    },
    {
      path: "/admin",
      Component: lazy(() => import("./routes/admin/page")),
    },
    {
      path: "/admin/mobile",
      Component: lazy(() => import("./routes/admin/mobile/page")),
    },
    {
      path: "/organizations",
      Component: lazy(() => import("./routes/organizations/page")),
    },
    {
      path: "/organizations/new",
      Component: lazy(() => import("./routes/organizations/new/page")),
    },
    {
      path: "/organizations/:id",
      Component: lazy(() => import("./routes/organizations/[id]/page")),
    },
    {
      path: "/organizations/:id/members",
      Component: lazy(
        () => import("./routes/organizations/[id]/members/page")
      ),
    },
    {
      path: "/organizations/:id/settings",
      Component: lazy(
        () => import("./routes/organizations/[id]/settings/page")
      ),
    },
    {
      path: "/invitations/accept",
      Component: lazy(() => import("./routes/invitations/accept/page")),
    },
  ],
  marketingRoutes: [
    {
      path: "/terms",
      Component: lazy(() => import("./routes/terms/page")),
    },
    {
      path: "/privacy",
      Component: lazy(() => import("./routes/privacy/page")),
    },
    {
      path: "/acceptable-use",
      Component: lazy(() => import("./routes/acceptable-use/page")),
    },
    {
      path: "/responsible-use",
      Component: lazy(() => import("./routes/responsible-use/page")),
    },
  ],
  navItems: [
    { href: "/billing", label: "Billing" },
    { href: "/admin", label: "Admin", superuserOnly: true },
    { href: "/organizations", label: "Organizations" },
  ],
  profilePanels: [],
  services: {},
});
