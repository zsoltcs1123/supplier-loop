# Implement the pure classer in the supplier-loop repo. Do not commit. Do not push. Do not mention Anneal, anneal entity c

- **Started:** Monday, Sep 21, 2026, 1:05 PM (UTC+2)
- **Session ID:** `c0f2c1f9-59d5-4aa2-a778-4a94134ce574`
- **Project:** `supplier-loop`
- **User turns:** 1
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/d6dcac54-a0ba-4ed5-a356-c25c512111e9/subagents/c0f2c1f9-59d5-4aa2-a778-4a94134ce574.jsonl`
- **Type:** subagent

---

## User 1

Implement the pure classer in the supplier-loop repo. Do not commit. Do not push. Do not mention Anneal, anneal entity codes, or Anneal concepts anywhere in source, tests, comments, or docs.

## Workspace

Absolute path: `/home/zs/repos/supplier-loop`
Python 3.11, uv. Package: `src/supplier_loop/`. Tests: `tests/`.

Read first: `PRINCIPLES.md`, `docs/SEED.md`, `docs/ARCHITECTURE.md`, `docs/spec/ESCALATION_RULES.md`, `DEVELOPING.md`, `.cursor/rules/python.mdc`, `.cursor/rules/python-testing.mdc`.

Current HEAD already has: in-memory simulator, round state (`QuoteRecord`, `RfqContext`, `SupplierFacts`, `DedupRegistry`), mail kind classifier, extract port + fixture mock, quote pipeline (normalize + recompute). Reuse those types. Do not duplicate models.

## Outcome

Given a Quote record, RFQ context, price history, `injection_suspected`, and own quote history, code returns the set of required escalation classes. The classer does not write `auto_approved` or `action_taken`.

Done when:

1. A pure function classer covers rules 1 through 7 from `docs/spec/ESCALATION_RULES.md`.
2. Class 7 follows `injection_suspected` with no override. If the flag is true, class 7 is always in the result — even when you believe it is a false positive. If the flag is false, do not add class 7.
3. Unit tests assert classes only. They do not assert `action_taken`, `auto_approved`, sent mail, or phases.

Out of scope: sending mail, lifecycle phases, submit flags, orchestrator, machine (`correct_once`, `negotiate_once`, reminders), MCP, OpenRouter.

## Rules (exact)

From `docs/spec/ESCALATION_RULES.md` and `docs/SEED.md`:

1. Missing BOM line — only when the line is in the BOM **and** in that supplier's catalog (`directory[].material_ids`) **and** absent from the quote. Extra materials the supplier sent are not class 1.
2. Quantity differs from the matching BOM line quantity.
3. Payment terms differ from `assignment.required_payment_terms`.
4. Validity is **shorter** than `assignment.required_validity_days`. Equal or longer is fine.
5. A unit price is above that supplier's last accepted price (`get_price_history()` / `rfq.price_history` for that supplier_id + material_id) by more than `assignment.target_price_ceiling_pct`. Compare against that supplier's history row, not a global average.
6. Negotiation / pushback outcome. Input includes `own_quote_history`. If that history is non-empty (a negotiation exchange was recorded), require class 6. Do not implement negotiate_once here; just classify from the history you are given. Arithmetic differences are not class 6.
7. Instruction embedded in supplier content: follow `injection_suspected` only. Never skip class 7 because you think the flag is wrong. Never scan prose yourself to add or remove class 7.

Do NOT escalate (must not appear as classes):
- Arithmetic errors (line total ≠ qty × unit_price, grand total ≠ sum). Already handled by recomputed totals in the quote pipeline.
- Duplicates.
- Silence / reminders.
- Clarifying questions.

Use `revised_as_sent` when present; otherwise `as_sent`. That is the document the classer sees.

Match quote lines to BOM by `material_id` after normalize (pipeline already fills material_id from description when unambiguous). If a quote line still has no material_id, it cannot satisfy a BOM line.

Return a set (or frozen set) of int class numbers. Order does not matter. Empty set means no required classes.

You will need `supplier_id` to look up catalog materials and that supplier's price history. `RfqContext` has `directory` and `price_history`. Architecture lists classer inputs as Quote record, RFQ context, price history, injection_suspected, own quote history — passing `supplier_id` (or `SupplierFacts`) is fine and necessary.

`injection_suspected` is on the extract result, not on `QuoteRecord`. Pass it as an argument; do not stuff it onto QuoteRecord.

## Existing types

```
src/supplier_loop/round_state/models.py
  QuoteRecord, AsSentQuote, QuoteLine, RfqContext, SupplierFacts
src/supplier_loop/simulator/port.py
  Assignment, BomLine, SupplierEntry, PriceHistoryRow
src/supplier_loop/extract/schema.py
  ExtractResult.injection_suspected
```

Suggested layout: `src/supplier_loop/classer/` with a pure `required_classes(...)` function. Tests under `tests/unit/classer/`.

## Tests

- `@pytest.mark.unit`. Names: `test_<subject>_<expected_behavior>_when_<condition>`.
- Parametrize boundaries for ceiling (at ceiling vs above), validity (equal vs shorter), missing line only when supplier carries the material.
- Class 7 present iff `injection_suspected` is true, including when other classes are empty and when they are not.
- Class 6 when own_quote_history is non-empty; absent when empty.
- Arithmetic-wrong quote does not add a class by itself.
- No `monkeypatch.setattr` on first-party modules. Build real QuoteRecord / RfqContext fixtures.
- Do not test language features. Do not assert mail or submit flags.

## Constraints

- Surgical. No drive-by refactors. No comments. No docstrings except public API.
- Absolute imports. Type hints on everything. Prefer functions over classes.
- Pydantic already used for schemas; classer should be a pure function.
- Do not leak Anneal identifiers into the repo.

## Verify

1. `uv run ruff format` and `uv run ruff check` on touched paths
2. `uv run mypy` on touched packages
3. `uv run pytest -m unit`
4. Prefer `uv run prek run --all-files` if it stays reasonable

Fix failures you introduce.

## Return to parent

Single report: what landed, file list, test results, leftover risks (title + 1 line). Do not use the anneal CLI. Confirm no git commit. Do not implement work beyond the classer.

## Assistant

Me read spec and existing types first, then build pure classer.

[REDACTED]
[tool: UpdateCurrentStep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Glob]
[tool: Glob]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Me build classer module and tests now.

[REDACTED]
[tool: UpdateCurrentStep]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]

## Assistant

[REDACTED]
[tool: UpdateCurrentStep]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Read]
[tool: Shell]

## Assistant

Test helper treat empty list as falsy — me fix that.

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Shell]
[tool: Shell]

## Assistant

[REDACTED]
[tool: UpdateCurrentStep]

## Assistant

## Report for parent

### What landed

Pure classer at `supplier_loop.classer.required_classes(...)`.

- Input: `QuoteRecord`, `RfqContext`, `supplier_id`, `injection_suspected`, `own_quote_history`
- Output: `frozenset[int]` of required escalation classes
- Uses `revised_as_sent` when present, else `as_sent`
- Rules 1–6 from code; rule 7 only from `injection_suspected` flag
- No `action_taken`, `auto_approved`, mail, or phase logic

### Files

| Path | Role |
|---|---|
| `src/supplier_loop/classer/classify.py` | `required_classes()` + helpers |
| `src/supplier_loop/classer/__init__.py` | Public export |
| `tests/unit/classer/__init__.py` | Package marker |
| `tests/unit/classer/test_classify.py` | 18 unit tests |

### Test results

- `uv run pytest -m unit tests/unit/classer/` — **18 passed**
- `uv run pytest -m unit` — **94 passed** (5 deselected integration)
- `uv run ruff format` / `ruff check` — **passed**
- `uv run mypy src/supplier_loop/classer/` — **passed**
- `uv run prek run --all-files` — **all hooks passed**

### Leftover risks

| Risk | Note |
|---|---|
| Payment terms matching | Exact string compare; no normalization if supplier uses variant spelling |
| Float quantity compare | Uses `!=`; tiny float drift on BOM qty could false-trigger class 2 |
| Missing price history row | Class 5 skipped when no history for that supplier+material; may be right but untested edge |

### Git

**No commit. No push.** Untracked only: `src/supplier_loop/classer/`, `tests/unit/classer/`.

[REDACTED]
