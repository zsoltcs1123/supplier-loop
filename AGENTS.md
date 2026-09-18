# AGENTS.md

> Baseline guidance for AI coding agents. For detailed python standards see `.cursor/rules/`.

**supplier-loop**: Python 3.11, uv. Main package at `src/supplier_loop/`, workspace members under `packages/`.

Design and runtime constraints live in `SEED.md`. Spec files are under `docs/spec/`; fixtures under `docs/fixtures/`.

## Development loop

Read `PRINCIPLES.md`, `SEED.md`, and `DEVELOPING.md` before coding work, answering queries or giving advice.
Iterate with path-local ruff/mypy (`src/supplier_loop` or `packages/<pkg>`). Canonical gate: `uv run prek run --all-files`.
Commit only after the gate. Commit rules: `DEVELOPING.md`.
