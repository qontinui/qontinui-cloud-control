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
npm ci
npm run cloud:install    # links this repo into node_modules
npm run dev
```

`npm run cloud:status` reports which shape the tree is in and
`npm run cloud:remove` returns it to OSS-only. Re-run `cloud:install` after any
`npm install` / `npm ci`, which prune the link as extraneous.

This package ships raw `.ts`/`.tsx` with no build step, and compiles **inside**
the host app — that is what makes the `@/...` imports in these sources (the
host's alias, e.g. `@/lib/extension-slots`) resolve. qontinui-web enables that
with `transpilePackages` when the link is present. A `"use client"` boot module
in its root layout performs the side-effect import, so registration lands in
the **browser's** module instance of the slot registry, which is the one every
consumer reads.

The full contract — how the two build shapes are wired, the CI job that gates
the composed one, and the two defects this replaced (an unresolvable
`webpackIgnore` import, evaluated in a Server Component, with its failure
swallowed by `.catch(() => {})`) — is in
[`qontinui-web/frontend/docs/composed-cloud-build.md`](https://github.com/qontinui/qontinui-web/blob/main/frontend/docs/composed-cloud-build.md).

Note that npm is the only supported package manager here: qontinui-web's
`preinstall` runs `npx only-allow npm`.

## License

Licensed under the **GNU Affero General Public License v3.0 or later** (`AGPL-3.0-or-later`). See [`LICENSE`](LICENSE) for the full text. Contributions are accepted under the Developer Certificate of Origin — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
