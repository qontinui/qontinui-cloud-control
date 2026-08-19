/**
 * qontinui-cloud-control — cloud frontend extension to qontinui-web (AGPL-3.0-or-later).
 *
 * Importing this package side-effect-registers cloud-control's service and
 * component slots with the OSS extension surface (`@/lib/extension-slots`).
 *
 * ROUTES AND NAV ENTRIES DO NOT COME FROM HERE. They used to — as `appRoutes`
 * / `marketingRoutes` / `navItems` arrays in this call — and nothing ever read
 * them: Next builds the App Router from the filesystem at build time, and the
 * host's sidebar builds its item list from static modules, so a runtime array
 * of either could never take effect. The host now mounts routes with one-line
 * re-export shims under `app/(app)/` and reads sidebar entries from
 * `./nav-items.ts`, both resolved at build time through its `@cloud` alias.
 *
 * ROUTE FILE NAMING IS LOAD-BEARING. Every route is `routes/<path>/page.tsx`,
 * mirroring the App Router, and the host's `cloud-route-shims` test treats
 * exactly that set as the route inventory — every such file must either have
 * a host shim or be named in the test's `UNMOUNTED` list with a reason. That
 * is what replaced the old `appRoutes` array as the source of truth, so a
 * route added as `routes/foo.tsx` is invisible to the guard. Supporting
 * modules live in `_components/` / `_hooks/` or under any name that is not
 * `page.tsx`. See the host's `frontend/docs/composed-cloud-build.md`.
 *
 * HOST IMPORTS USE `@/`, NOT `@qontinui/web/`. There is no package named
 * `@qontinui/web` anywhere in the workspace — qontinui-web's frontend
 * package.json declares `"name": "frontend"`, and neither its tsconfig
 * `paths` nor its next.config webpack `resolve.alias` maps that specifier.
 * This module is compiled INSIDE the host app, so `@/...` (the host's only
 * alias, `./src/*`) is the convention every other file here already uses.
 * Getting this wrong used to be silent: `layout.tsx` loaded this package with
 * `import(...).catch(() => {})`, under which a resolution failure was
 * indistinguishable from "cloud-control is not installed" and every extension
 * below simply never registered. The host now uses a static import from
 * `components/cloud-extensions-boot.tsx`, so it is a build error.
 *
 * `@/services/service-factory` resolves to the SAME module instance as the
 * `@/lib/extension-slots` imported here, which is what makes the service
 * registration below land in the registry the OSS `getService()` reads.
 */

import type { ComponentType } from "react";
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
  // would fork the auth-refresh path. Safe at module scope: the host imports
  // this package from `components/cloud-extensions-boot.tsx`, a different
  // module from `service-factory`, so the factory has already evaluated by
  // the time this line runs.
  services: {
    billingService: new BillingService(httpClient),
    organizationService: new OrganizationService(httpClient),
  },
  // Inline component slots — the OSS shell renders these with
  // `useSlotComponent(slot)` when the cloud-control bundle has loaded, and
  // nothing in OSS-only deploys. These stay while the route/nav arrays go:
  // a component reference is a genuine runtime *value*, with no build-time
  // filesystem or module-graph contract to satisfy.
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
