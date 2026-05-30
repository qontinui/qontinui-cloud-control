# qontinui-cloud-control

**Open source (AGPL-3.0-or-later).** Cloud extension to qontinui-web.

This repo contains the cloud layer that powers the [qontinui.cloud](https://qontinui.cloud) deployment of qontinui-web. It composes on top of the [`qontinui-web`](https://github.com/qontinui/qontinui-web) frontend by side-effect-registering routes, models, services, components, and permission checks via the OSS extension surface (`app.extensions` on the backend, `lib/extension-slots.ts` on the frontend).

Self-hosters never need to run this code — the qontinui.cloud product is the deployment that includes it — but the source is open: the value of the hosted product is operating it (managed convenience, scale, and the per-customer knowledge moat), not withholding billing/multi-tenant CRUD. The monetizable concurrent-coordination layer lives in the closed `qontinui-coord` service, not here.

## What lives here

* Stripe billing flow (checkout, webhooks, subscription mapping)
* Multi-tenant routing (organizations list/switch/invite UIs)
* Cloud-admin pages (cross-tenant users, projects, analytics, fleet health)
* Cross-tenant audit-log endpoints
* qontinui.cloud-specific marketing/legal pages (Terms, Privacy, AUP, Responsible Use)
* Beta-signup flow

## Composition pattern

Sentry-style: `getsentry/sentry` (OSS) + `getsentry/getsentry` (private SaaS). qontinui-cloud-control monkey-patches the OSS extension hooks at install time.

Required sibling-repo layout:

```
qontinui-root/
├── qontinui-web/         (OSS, AGPL-3.0)
└── qontinui-cloud-control/   (this repo, OSS, AGPL-3.0)
```

Cloud-control developers always need qontinui-web checked out as a sibling; OSS contributors never need cloud-control.

## Backend

```
cd qontinui-cloud-control
pip install -e ../qontinui-web/backend
pip install -e .
uvicorn app.main:app
```

The OSS `app.main:app` entry-point is reused as-is. Cloud-control attaches itself by being importable from the same Python interpreter.

## Frontend

```
cd qontinui-web/frontend
pnpm install --link ../../qontinui-cloud-control/frontend
pnpm dev
```

OSS's `layout.tsx` dynamic-imports `@qontinui/cloud-control`; the import is silently no-op'd when the package isn't linked.

## License

Licensed under the **GNU Affero General Public License v3.0 or later** (`AGPL-3.0-or-later`). See [`LICENSE`](LICENSE) for the full text. Contributions are accepted under the Developer Certificate of Origin — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
