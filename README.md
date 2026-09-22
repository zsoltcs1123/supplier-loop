# Supplier Loop

Automated supplier-quoting loop for the LeadFlow Automation challenge. The loop talks to a live MCP simulator: read RFQs, email suppliers, extract and validate quotes, escalate when required, and submit results.

Python 3.11, managed with [uv](https://github.com/astral-sh/uv).

## Run

One command. Python 3.11. The loop sends the RFQs, polls, and calls `submit_results`. Do not send mail by hand.

```bash
uv run python -m supplier_loop run-dev
```

Put credentials in `.env` first (see Setup). The loop contract is [docs/LOOP_CONTRACT.md](docs/LOOP_CONTRACT.md).

## Setup

```bash
uv sync --dev && uv pip install -e .
prek install --hook-type pre-commit --hook-type commit-msg
```

Copy `.env.example` to `.env` and fill in credentials when you have them. The live names are `SUPPLIER_SIM_MCP_URL`, `SUPPLIER_SIM_TOKEN`, and optionally `OPENROUTER_API_KEY` / `OPENROUTER_MODEL`. `OPENROUTER_MODEL` defaults to `google/gemini-2.5-pro`. `run-dev` needs the OpenRouter key. Spend against the $100 cap is recorded in `.artifacts/llm-spend.json`. Email bodies carry watermarks: set `PYTHONIOENCODING=utf-8`.

```bash
uv run python -m supplier_loop ping      # MCP connectivity; does not start a round
uv run python -m supplier_loop run-dev   # request_dev_round, then loop until submit_results
uv run python -m supplier_loop resume-dev  # continue the current round, including after you start the exam
uv run python -m supplier_loop pack-propose  # dump a proposal pack from round files; no MCP, no OpenRouter
```

`ping` must succeed before `run-dev`. `request_dev_round` is capped at 20 calls per token. `run-dev` records each call in [dev-rounds.json](dev-rounds.json). Ping does not count.

`pack-propose` reads `.artifacts/round/round.json`, `.artifacts/ops.jsonl`, and `.artifacts/llm-spend.json`. It writes `.artifacts/proposals/<round_id>/pack.md`. Run it after a finished development round, not during the exam. The quoting loop never calls it. How to write a proposal: [docs/proposals/PROMPT.md](docs/proposals/PROMPT.md).

The loop never calls `start_exam`. Only you do, out of band. After you start the exam, run `resume-dev` against that round. Set `PYTHONIOENCODING=utf-8` so email watermarks print.

Measured live-round numbers and known weaknesses: [SELF-EVALUATION.md](SELF-EVALUATION.md).

## Development

See **[DEVELOPING.md](DEVELOPING.md)** for commands, hooks, and commit conventions.

```bash
uv run ruff format .     # Format
uv run ruff check .      # Lint
uv run mypy .            # Type check
uv run pytest            # Test
prek run --all-files     # All pre-commit hooks
```

## Project structure

```
supplier-loop/
├── src/supplier_loop/     # Main package
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── SEED.md            # Design seed and repo bootstrap notes
│   ├── ARCHITECTURE.md    # Components, trust boundary, runtime shape
│   ├── spec/              # Challenge spec files
│   └── fixtures/          # Sample traffic and example artifacts
└── packages/              # Workspace members
```

## Documentation

- **[docs/SEED.md](docs/SEED.md).** Design decisions, loop pass, bootstrap steps.
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).** Components, trust boundary, runtime shape.
- **[DEVELOPING.md](DEVELOPING.md)** — development tools and workflows
- **[AGENTS.md](AGENTS.md)** — AI coding agent guidance
- **`docs/spec/`** — challenge brief, RFQ format, escalation rules, and related spec

## License

MIT
