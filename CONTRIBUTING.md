# Contributing to qontinui-cloud-control

Thanks for your interest in contributing. This document explains how to submit changes and what you're agreeing to when you do.

## License & contributions

This project is licensed under the **GNU Affero General Public License v3.0 or later** (`AGPL-3.0-or-later`). See [`LICENSE`](LICENSE) for the full text. Contributors should be aware:

- AGPL is a strong copyleft license. Anyone who runs a modified version of this project as a network service must offer its users the Corresponding Source under AGPL too.
- For typical self-hosting, internal use, forking, or contributing back, AGPL behaves like GPL.

Contributions are accepted under the **Developer Certificate of Origin (DCO) 1.1** — *not* a CLA. The DCO text lives in [`DCO.txt`](DCO.txt). Certify that you wrote (or otherwise have the right to submit) your contribution by adding a `Signed-off-by` trailer to every commit:

    git commit -s -m "your message"

which appends `Signed-off-by: Your Name <your@email>` from your `git config user.name` / `user.email`. Your contributions are licensed inbound under the same `AGPL-3.0-or-later` as the project (inbound = outbound); you retain copyright in your contributions. No relicensing rights are granted — the dual-/commercial-license lever is retained only on the embeddable `ui-bridge` library (via its CLA), not on the apps in this repository.

## Boundary

cloud-control is the open cloud extension to [`qontinui-web`](https://github.com/qontinui/qontinui-web). It composes on top of the OSS web frontend/backend via the extension surface. It must **not** import the closed `qontinui-coord` service source — the monetizable concurrent-coordination layer lives behind the coord wall, and a lint guard (`scripts/check_no_coord_import.py`, run in CI) fails the build if a coord import is ever introduced. If cloud-control needs to talk to coord, do it over coord's network API, not by importing its source.

## Submitting a change

1. Fork the repository and create a feature branch.
2. Make your change. Add tests where appropriate (`vitest` on the frontend, `pytest` on the backend).
3. Run the local checks (lint, format, tests) — the `README` documents the exact commands.
4. Open a pull request against `main`. Describe the *why* in the PR body, not the *what*.
5. Ensure every commit carries a `Signed-off-by` trailer (`git commit -s`) — the DCO bot checks this.
6. A maintainer will review.

## Code of conduct

Be kind. Be specific. No harassment. Discussions stay on the technical merits.
