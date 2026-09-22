# SL-V9 — Proposal pack dumps a finished round without spending the extract key

**Status:** active

**Path:** SL

## Scenarios

- Given .artifacts/round/`round.json` and .artifacts/`ops.jsonl` from a finished round, uv run python `-m` supplier_loop pack-propose writes .artifacts/proposals/<round_id>`/pack.md` that contains the round id, per-supplier phases, and the allow-list. .artifacts/llm-`spend.json` field used is unchanged.
- uv run python `-m` supplier_loop `--help` lists pack-propose. run-dev and resume-dev still exist as the quoting entry points.

## Coverage

src/supplier_loop/`cli.py`, src/supplier_loop/`propose.py`, src/supplier_loop/operational_log/`log.py`, docs/proposals/`**PROMPT**`.md

## Lifecycle

active
