/**
 * qontinui-cloud-control — cloud frontend extension to qontinui-web (AGPL-3.0-or-later).
 *
 * Importing this package side-effect-registers cloud-control routes,
 * components, services, and contexts with the OSS extension surface
 * (`@/lib/extension-slots`).
 *
 * HOST IMPORTS USE `@/`, NOT `@qontinui/web/`. There is no package named
 * `@qontinui/web` anywhere in the workspace — qontinui-web's frontend
 * package.json declares `"name": "frontend"`, and neither its tsconfig
 * `paths` nor its next.config webpack `resolve.alias` maps that specifier.
 * This module is compiled INSIDE the host app, so `@/...` (the host's only
 * alias, `./src/*`) is the convention every other file here already uses.
 * Getting this wrong is silent: `layout.tsx` loads this package with
 * `import(...).catch(() => {})`, so a resolution failure is indistinguishable
 * from "cloud-control is not installed" and every extension below simply
 * never registers.
 *
 * `@/services/service-factory` resolves to the SAME module instance as the
 * `@/lib/extension-slots` imported here, which is what makes the service
 * registration below land in the registry the OSS `getService()` reads.
 */

import { lazy, type ComponentType } from "react";
import { registerCloudExtensions } from "@/lib/extension-slots";
import { httpClient } from "@/services/service-factory";
import { OrganizationSwitcher } from "./components/collaboration/OrganizationSwitcher";
import { CreateOrganizationDialog } from "./components/collaboration/CreateOrganizationDialog";
import { TeamMemberList } from "./components/collaboration/TeamMemberList";
import { InviteMemberDialog } from "./components/collaboration/InviteMemberDialog";
import { BetaBanner } from "./components/beta-banner";
import { SubscriptionBadge } from "./components/subscription-badge";
import { BillingService } from "./services/billing-service";
import { OrganizationService } from "./services/collaboration/organization-service";

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
  // Marketing routes. `/terms`, `/acceptable-use` and `/responsible-use`
  // were registered here as copies that are byte-identical (modulo a BOM and
  // CRLF endings) to the pages qontinui-web already serves at those paths to
  // everyone, cloud and self-hosted alike. Two copies of a legal document is
  // a drift hazard with no upside — PR #9 edited the OSS side and happened
  // not to diverge them only because both were touched — so the copies are
  // deleted and the OSS pages are the single source.
  //
  // `/privacy` is NOT the same case and is deliberately left unresolved:
  // cloud-control's policy is 326 lines against OSS's 92, i.e. a genuinely
  // different document describing the hosted service's data handling. Which
  // one a cloud deployment must serve is a legal/compliance decision, not an
  // engineering one, and it is open in
  // 2026-08-08-cloud-extension-route-mounting's "Open questions". Its page
  // stays in the tree, unmounted — the OSS page is what every deployment
  // serves today, so this preserves current behaviour rather than picking a
  // policy by default. Do not mount it without that decision.
  marketingRoutes: [],
  navItems: [
    { href: "/billing", label: "Billing" },
    { href: "/admin", label: "Admin", superuserOnly: true },
    { href: "/organizations", label: "Organizations" },
  ],
  profilePanels: [],
  // Service slots — the OSS `ServiceFactory` wires `billingService` and
  // `organizationService` as `cloudOnlySlot(...)` Proxies that resolve
  // `getService(name)` on every property access. Until these were registered
  // the Proxies threw "…is only available in the cloud-control deployment"
  // IN THE CLOUD DEPLOYMENT TOO, because nothing ever filled the slots —
  // 26 live call sites drove them. 16 in OSS (`hooks/useOrganization.ts`,
  // `contexts/collaboration-context.tsx`,
  // `contexts/collaboration/OrganizationContext.tsx`,
  // `automation-builder/hooks/useProjectSharing.ts`) and 10 in THIS package,
  // which reaches its own services back through the host factory:
  // `routes/pricing.tsx`, `routes/organizations/[id]/{page,settings/page}.tsx`,
  // `routes/organizations/[id]/members/_hooks/useMembersPage.ts` and
  // `contexts/organization-context.tsx`. Every method those sites call
  // (`getSubscription`, `redirectToCheckout`, `getOrganization(s)`,
  // `createOrganization`, `updateOrganization`, `deleteOrganization`,
  // `getStatistics`, `getMembers`, `inviteMember`, `updateMemberRole`,
  // `removeMember`) exists on the two classes below.
  //
  // Constructed eagerly with the host's shared `httpClient` so both services
  // reuse the one TokenManager/TokenRefreshService — a second HttpClient
  // would fork the auth-refresh path. Safe at module scope: OSS loads this
  // package by dynamic `import()` from `layout.tsx`, long after
  // `service-factory` has evaluated.
  services: {
    billingService: new BillingService(httpClient),
    organizationService: new OrganizationService(httpClient),
  },
  // Inline component slots — OSS shell renders these via `getComponent(slot)`
  // when the cloud-control bundle has loaded, or nothing in OSS-only deploys.
  // Cast to `ComponentType<unknown>` because the slot Map stores opaque
  // components; OSS consumers re-cast to their declared prop interface
  // (see `qontinui-web/frontend/src/lib/cloud-component-slots.ts`).
  components: {
    organizationSwitcher: OrganizationSwitcher as ComponentType<unknown>,
    createOrganizationDialog: CreateOrganizationDialog as ComponentType<unknown>,
    teamMemberList: TeamMemberList as ComponentType<unknown>,
    inviteMemberDialog: InviteMemberDialog as ComponentType<unknown>,
    betaBanner: BetaBanner as ComponentType<unknown>,
    subscriptionBadge: SubscriptionBadge as ComponentType<unknown>,
  },
});
