# qontinui-cloud-control

**Proprietary, cloud-only.** Not open source. Not redistributable.

This repo contains the cloud-only layer that powers the [qontinui.cloud](https://qontinui.cloud) deployment of qontinui-web. It composes on top of the OSS [`qontinui-web`](https://github.com/jspinak/qontinui-web) frontend by side-effect-registering routes, models, services, components, and permission checks via the OSS extension surface (`app.extensions` on the backend, `lib/extension-slots.ts` on the frontend).

Self-hosters never run this code. The cloud product is the only deployment that includes it.

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
├── qontinui-web/         (OSS, AGPL-v3)
└── qontinui-cloud-control/   (this repo, proprietary)
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

## Reference docs

* `tmp_cloud_control_carve_out.md` (in qontinui-web's repo root) — full boundary design.
* `tmp_cloud_control_audit.md` — the OSS-vs-cloud-control verdict catalog that drove the carve-out.
* `tmp_qontinui_business_model.md` §4 — operate-don't-feature gating posture.
* `tmp_canonical_db_topology_plan.md` §4 — the `cloud.*` schema lives in OSS migrations; ORM classes here.
