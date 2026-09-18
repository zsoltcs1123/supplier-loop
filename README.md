# Supplier Loop

Automated supplier-quoting loop for the LeadFlow Automation challenge. The loop talks to a live MCP simulator: read RFQs, email suppliers, extract and validate quotes, escalate when required, and submit results.

Python 3.11, managed with [uv](https://github.com/astral-sh/uv).

## Setup

```bash
uv sync --dev && uv pip install -e .
prek install --hook-type pre-commit --hook-type commit-msg
```

Copy `.env.example` to `.env` and fill in credentials when you have them. See [docs/SEED.md](docs/SEED.md) for required env var names.

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
