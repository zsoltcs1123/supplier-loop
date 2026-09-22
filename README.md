# Supplier Loop

Automated supplier-quoting loop for the LeadFlow Automation challenge. Talks to a live MCP simulator: read RFQs, email suppliers, extract and validate quotes, escalate when required, submit results.

Python 3.11, managed with [uv](https://github.com/astral-sh/uv).

## Run

```bash
uv run python -m supplier_loop run-dev
```

The loop sends RFQs, polls, and calls `submit_results`. Do not send mail by hand. Put credentials in `.env` first (see Setup). Loop contract: [docs/LOOP_CONTRACT.md](docs/LOOP_CONTRACT.md).

## Setup

```bash
uv sync --dev && uv pip install -e .
prek install --hook-type pre-commit --hook-type commit-msg
```

Copy `.env.example` to `.env`. Live names: `SUPPLIER_SIM_MCP_URL`, `SUPPLIER_SIM_TOKEN`, and optionally `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` (default `google/gemini-2.5-pro`). `run-dev` needs the OpenRouter key. Spend against the $100 cap: `.artifacts/llm-spend.json`. Set `PYTHONIOENCODING=utf-8` for email watermarks.

```bash
uv run python -m supplier_loop ping         # MCP connectivity; no round
uv run python -m supplier_loop run-dev      # request_dev_round, loop until submit_results
uv run python -m supplier_loop resume-dev   # continue current round (also after start_exam)
uv run python -m supplier_loop pack-propose # proposal pack from round files; no MCP, no OpenRouter
```

`ping` before `run-dev`. `request_dev_round` capped at 20 per token; each `run-dev` call logged in [dev-rounds.json](dev-rounds.json). Ping does not count.

`pack-propose` reads `.artifacts/round/round.json`, `.artifacts/ops.jsonl`, `.artifacts/llm-spend.json`; writes `.artifacts/proposals/<round_id>/pack.md`. After a finished dev round only, not during the exam. The quoting loop never calls it. Proposal format: [docs/proposals/PROMPT.md](docs/proposals/PROMPT.md).

The loop never calls `start_exam`. Call it out of band, then `resume-dev`. Survives restarts; when server `round_id` changes, wipes local state and snapshots the new assignment before polling.

## Development

[DEVELOPING.md](DEVELOPING.md): commands, hooks, commit conventions.

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest
prek run --all-files
```

## Project structure

```
supplier-loop/
├── src/supplier_loop/
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── SEED.md
│   ├── ARCHITECTURE.md
│   ├── spec/
│   └── fixtures/
└── packages/
```

## Documentation

- [docs/SEED.md](docs/SEED.md) — design decisions, loop pass, bootstrap
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — components, trust boundary, runtime shape
- [DEVELOPING.md](DEVELOPING.md) — development tools
- [AGENTS.md](AGENTS.md) — AI coding agent guidance
- [WORKLOG.md](WORKLOG.md) — process record (tools, hours, phases)
- [SELF-EVALUATION.md](SELF-EVALUATION.md) — measured dev metrics, known weaknesses
- `docs/spec/` — challenge brief, RFQ format, escalation rules

## License

MIT
