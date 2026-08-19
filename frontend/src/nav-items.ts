import React from "react";
import { Building2, CreditCard } from "lucide-react";
import type { NavItem } from "@/components/navigation/sidebar/types";

/**
 * Sidebar entries contributed by the cloud deployment.
 *
 * Resolved by qontinui-web at build time through the `@cloud` alias
 * (`@cloud/nav-items`), the same mechanism that mounts the cloud routes —
 * see qontinui-web's `frontend/docs/composed-cloud-build.md`. The OSS stand-in
 * at `src/cloud-absent/nav-items.ts` exports an empty array, so a self-hosted
 * build gets no cloud entries and needs no runtime check.
 *
 * This replaces the `navItems` array formerly registered into the runtime
 * extension-slot registry, which nothing ever read: the sidebar builds its
 * item list synchronously from static modules, so a slot filled at
 * module-load time was never consulted.
 *
 * `/admin` was in that old array and is deliberately NOT here. qontinui-web's
 * own `devNavItems` already carries an `admin` item with the same route and
 * the same superuser gate, so contributing a second one would render the
 * entry twice in a composed build. The cloud `/admin` *route* is still
 * mounted — it is the page behind the OSS nav item that changes, not the nav.
 *
 * `adminOnly` is qontinui-web's spelling of what cloud-control's old slot
 * called `superuserOnly`; both mean "render only when
 * `user.is_superuser === true`" (`_hooks/use-sidebar-navigation.ts`).
 */
export const cloudNavItems: NavItem[] = [
  {
    id: "cloud-organizations",
    label: "Organizations",
    description: "Teams, members, and invitations",
    icon: React.createElement(Building2, { className: "size-5" }),
    route: "/organizations",
    color: "var(--brand-primary)",
    group: "Account",
  },
  {
    id: "cloud-billing",
    label: "Billing",
    description: "Plan, limits, and payment",
    icon: React.createElement(CreditCard, { className: "size-5" }),
    route: "/billing",
    color: "var(--brand-primary)",
  },
];
