# Supplier Loop

Automated supplier-quoting loop for the LeadFlow Automation challenge. The loop talks to a live MCP simulator: read RFQs, email suppliers, extract and validate quotes, escalate when required, and submit results.

Python 3.11, managed with [uv](https://github.com/astral-sh/uv).

## Setup

```bash
uv sync --dev && uv pip install -e .
prek install --hook-type pre-commit --hook-type commit-msg
```

Copy `.env.example` to `.env` and fill in credentials when you have them. The live names are `SUPPLIER_SIM_MCP_URL`, `SUPPLIER_SIM_TOKEN`, and optionally `OPENROUTER_API_KEY` / `OPENROUTER_MODEL`.

```bash
uv run python -m supplier_loop ping      # MCP connectivity; does not start a round
uv run python -m supplier_loop run-dev   # request_dev_round, then loop until submit_results
```

`ping` must succeed before `run-dev`. `request_dev_round` is capped at 20 calls per token. `run-dev` records each call in [dev-rounds.json](dev-rounds.json). Ping does not count.

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
