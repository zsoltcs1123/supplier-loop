# Implement mail-kind classification and the fixture quote pipeline in the supplier-loop repo. Do not commit. Do not push.

- **Started:** Monday, Sep 21, 2026, 12:51 PM (UTC+2)
- **Session ID:** `ede2bfed-fa7a-4f63-b662-0c87f91aa9aa`
- **Project:** `supplier-loop`
- **User turns:** 1
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/d6dcac54-a0ba-4ed5-a356-c25c512111e9/subagents/ede2bfed-fa7a-4f63-b662-0c87f91aa9aa.jsonl`
- **Type:** subagent

---

## User 1

Implement mail-kind classification and the fixture quote pipeline in the supplier-loop repo. Do not commit. Do not push. Do not mention Anneal, anneal entity codes, or Anneal concepts anywhere in source, tests, comments, docs, or commit messages.

## Workspace

Absolute path: `/home/zs/repos/supplier-loop`
Python 3.11, uv. Main package: `src/supplier_loop/`. Tests: `tests/`.

Read before coding: `PRINCIPLES.md`, `docs/SEED.md`, `docs/ARCHITECTURE.md`, `DEVELOPING.md`, `.cursor/rules/python.mdc`, `.cursor/rules/python-testing.mdc`.

## Outcome

Inbound fixture mail gets a kind from envelope and body shape. Only kind `quote` uses the extract port. The quote pipeline writes the Quote record. No live model.

Done when these deliverables exist and tests prove them:

1. Mail kind classifier: `quote`, `question`, `negotiation_reply`, `duplicate`, `approver_ruling`. Deterministic. Envelope + body shape. Dedup fingerprints do NOT live in the classifier; they live in round state. Classifier may *read* a passed-in registry/fingerprint set to emit `duplicate`, but must not own or persist it.
2. Extract port: thin Protocol. Fixture mock adapter for tests. Pydantic schema: quote fields plus `injection_suspected` only. `extra="forbid"`. `action_taken` and `auto_approved` MUST NOT be on the schema. No OpenRouter. No PDF text-layer reader (later change).
3. Quote record already exists in `src/supplier_loop/round_state/models.py` (`QuoteLine`, `AsSentQuote`, `QuoteRecord` with `as_sent`, `recomputed_total`, `recomputed_grand_total`, optional `revised_as_sent`). Reuse it. Do not duplicate models. The quote pipeline is the only writer of `QuoteRecord`.
4. Normalize and validate in code. Match quote lines on description when SKU/`material_id` is absent. Recompute line `total` as qty * unit_price and `grand_total` as sum of recomputed line totals. As-sent line quantities, unit prices, payment_terms, validity_days stay as extracted. Do not invent lines the supplier never sent. Do not read supplier prose after extract.
5. Tests:
   - Parser tests for mail kind against `docs/fixtures/sample_traffic/emails/` (JSON files + `index.csv`). Cover questions, negotiation replies with no table, duplicates, quotes (inline, pasted table, PDF-attached, photo-attached). Approver rulings may need a small synthetic fixture if sample traffic has none — from `approver@sim.local` with a terse decision.
   - Unit tests for recomputed totals (wrong arithmetic in fixture lines).
   - Negotiation must not change `line_items` here. That path waits for a later defect-path change. Test that a `negotiation_reply` kind does not call extract and does not rewrite an existing Quote record's `as_sent.line_items`.
   - Extra fields forbidden on extract schema (`action_taken`, `auto_approved`, unknown keys).
   - Only kind `quote` uses extract.

## Existing code you must reuse

- Simulator protocol + in-memory adapter: `src/supplier_loop/simulator/`
- Round state models + store: `src/supplier_loop/round_state/`
- Operational log: `src/supplier_loop/operational_log/`
- `QuoteRecord` already defined. `DedupRegistry` already has `email_ids`, `attachment_ids`, `quote_fingerprints`.
- `EmailMessage` in `simulator/port.py`.

Do not implement: classer, orchestrator, lifecycle machine, submitter, MCP adapter, OpenRouter, PDF text reader, reminder/correct/negotiate machine paths.

## Architecture constraints (from docs/ARCHITECTURE.md and docs/SEED.md)

- Classifier kinds: quote, question, negotiation reply, duplicate, approver ruling. Only `quote` uses extract.
- Extract schema: quote fields + `injection_suspected`. Extra forbidden. Model never sees action fields.
- Quote pipeline chooses extract input. For this change, pass raw email body (and maybe filename/mime of attachments) to the fixture mock. Do not add PyMuPDF or OpenRouter.
- Pipeline is the only writer of the Quote record.
- After extract, code does not read supplier prose to decide.
- After negotiation, `line_items` stay the original document. Do not write a negotiated figure into line items. Do not implement negotiate_once; just do not mutate lines.
- Match on description when SKU absent (`docs/spec/RFQ_FORMAT.md`).
- Do not strip email watermarks.
- Keep PYTHONIOENCODING utf-8 in mind; bodies have zero-width / watermark chars.
- Surgical: touch only what this change needs. No drive-by refactors. No comments. No docstrings except public API. Absolute imports. Type hints on everything. Prefer functions over classes except Pydantic schemas and the existing adapter/store pattern.
- Tests: `@pytest.mark.unit` for pure/fast; parser tests against fixture files are still unit if they only read local JSON (no services). Name tests `test_<subject>_<expected_behavior>_when_<condition>`. No monkeypatch against first-party modules. No wiring-only tests. Prefer real fixture objects over mocks.

## Sample traffic (expected kinds, grounded in files)

Directory: `docs/fixtures/sample_traffic/emails/`

- Questions (no quote table): `005_p01_question-before-quoting-rfq-004.json`, `006_p02_rfq-rfq-001-one-question-before-we-quote.json`
- Negotiation replies (number-only / "can we meet in the middle", no table): `004_p01_re-can-we-meet-in-the-middle-rfq-003.json`, `018_p04_re-can-we-meet-in-the-middle-rfq-002.json`
- Quotes with inline lines: `001_p01_re-rfq-rfq-001-request-for-quote.json` and similar
- Quotes with pasted tables: `007_p02_fwd-rfq-001-quotation.json` and similar
- Quotes with PDF attachments: `011_p03_quote-for-rfq-rfq-001.json`, `012_p03_quote-for-rfq-rfq-001.json` (same subject/sender as 011 — treat as duplicate of prior quote when fingerprint/registry says already seen)
- Quotes with photo attachments: `016_p04_your-rfq-rfq-001-offer.json` and similar
- Duplicate: same quote sent twice keeps one entry. Classifier emits `duplicate` when a quote fingerprint is already in the passed-in registry. Fingerprint ownership stays in round state.

Read a handful of the JSON files to tune shape heuristics. Do not overfit to one supplier's prose. Prefer envelope (from, subject, attachments) + body shape (presence of qty/price table vs a question vs a plain number total in a meet-in-the-middle thread).

Approver email is `approver@sim.local`.

Extract fixture mock: tests inject structured extract results keyed by email id or by whatever the pipeline passes. Production OpenRouter adapter is out of scope; a stub that raises or is unimplemented is fine as long as tests use the fixture mock.

## Quote field shape (extract schema)

Align with existing models:

```
line_items: list of { material_id: str | None, description: str, quantity: float, unit_price: float, total: float }
payment_terms: str
validity_days: int
grand_total: float
injection_suspected: bool
```

Pipeline then builds `QuoteRecord`:
- `as_sent` from extract (as-sent numbers)
- `recomputed_total` / `recomputed_grand_total` from code arithmetic
- `revised_as_sent` left None in this change

Normalize: if `material_id` is None/absent, match `description` against RFQ BOM / catalog descriptions to fill `material_id` on as_sent when unambiguous. Do not invent materials.

## Suggested module layout (adjust if a simpler layout is better)

- `src/supplier_loop/mail_kind/` — classifier + kind Literal
- `src/supplier_loop/extract/` — Extract schema, Protocol, fixture mock
- `src/supplier_loop/quote_pipeline/` — normalize, recompute, write QuoteRecord; calls extract only for quote

Mirror tests under `tests/unit/...`.

## Verify

After implementation:

1. `uv run ruff format` on touched paths
2. `uv run ruff check` on touched paths
3. `uv run mypy` on touched packages
4. `uv run pytest -m unit` (and integration if you added any)
5. If time: `uv run prek run --all-files`

Fix any failures you introduced.

## Return to parent

A single report:

- What landed (modules, key functions, kinds heuristics)
- File list (added/modified)
- Test commands and pass/fail
- Any leftover risks or deferred items (title + 1 line). Do not use the anneal CLI.
- Confirm no git commit was made.

Do not implement work beyond this change. Do not create markdown docs unless a test fixture JSON is required.

## Assistant

I'll start by reading the project docs and existing code so the classifier and quote pipeline match the repo's constraints.
[tool: UpdateCurrentStep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Docs are in. Next I’ll inspect existing models, simulator ports, and the sample emails so the new modules fit what’s already there.
[tool: UpdateCurrentStep]
[tool: Read]
[tool: Glob]
[tool: Glob]
[tool: Glob]
[tool: Read]
[tool: Glob]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: GetDynamicTools]
[tool: Glob]

## Assistant

[tool: Read]
[tool: CallDynamicTool]
[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: CallDynamicTool]
[tool: CallDynamicTool]
[tool: Grep]
[tool: Read]

## Assistant

[tool: CallDynamicTool]
[tool: Read]
[tool: Glob]

## Assistant

I have the shape. Next I’ll add the classifier, extract port, and quote pipeline, then pin them with fixture tests.
[tool: UpdateCurrentStep]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]

## Assistant

[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: StrReplace]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: Write]
[tool: Write]
[tool: Write]

## Assistant

The classify coverage test is messy. I’ll clean that helper and write the extract and pipeline tests.
[tool: StrReplace]
[tool: StrReplace]
[tool: Write]
[tool: Write]

## Assistant

[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: Write]

## Assistant

[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]

## Assistant

[tool: Read]
[tool: Read]
[tool: StrReplace]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: UpdateCurrentStep]
[tool: Grep]
[tool: Grep]
[tool: Shell]

## Assistant

[tool: StrReplace]
[tool: Read]

## Assistant

[tool: Shell]

## Assistant

[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]
[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]
[tool: Glob]
[tool: Glob]
[tool: Glob]

## Assistant

[tool: UpdateCurrentStep]

## Assistant

Mail-kind classification and the fixture quote pipeline are in. Only kind `quote` calls extract and writes `QuoteRecord`. No git commit was made.

## What landed

**Classifier** (`classify_mail`): kinds `quote`, `question`, `negotiation_reply`, `duplicate`, `approver_ruling`.

Heuristics:
- `approver_ruling` — `from` is `approver@sim.local`
- `question` — no price table, no quote attachment; subject has “question” or body has `?`
- `negotiation_reply` — no table/artifact; “meet in the middle” in subject/body
- `quote` — ≥2 priced item lines, or attachments plus quote/quotation/offer/pricing words
- `duplicate` — quote-shaped, and the passed-in fingerprint is already in the registry

Fingerprints live in round state (`quote_fingerprint` = `from|subject`). The classifier only reads a set; it does not own or persist it.

**Extract port:** `Extractor` Protocol, `FixtureExtractor` (keyed by email id), `UnimplementedExtractor` stub. Schema is quote fields plus `injection_suspected`, `extra="forbid"`. Reuses `QuoteLine`. No `action_taken` / `auto_approved`. No OpenRouter. No PDF reader.

**Quote pipeline** (`process_inbound_mail`): classifies, extracts only for `quote`, matches description → `material_id` when unambiguous, recomputes line total as qty × unit_price and grand total as that sum, writes `QuoteRecord`. As-sent qty/price/terms/validity stay as extracted. Negotiation/question/duplicate/approver do not extract and do not rewrite `as_sent.line_items`.

## File list

Added:
- `src/supplier_loop/mail_kind/` — `__init__.py`, `classify.py`
- `src/supplier_loop/extract/` — `__init__.py`, `schema.py`, `port.py`, `fixture.py`
- `src/supplier_loop/quote_pipeline/` — `__init__.py`, `pipeline.py`, `normalize.py`, `recompute.py`
- `src/supplier_loop/round_state/fingerprint.py`
- `tests/unit/mail_kind/` — tests + `fixtures/approver_ruling.json`
- `tests/unit/extract/test_schema.py`
- `tests/unit/quote_pipeline/` — ingest, normalize, recompute tests
- `tests/unit/round_state/test_fingerprint.py`
- `tests/unit/sample_traffic.py`

Modified:
- `src/supplier_loop/round_state/__init__.py` (export `quote_fingerprint`)

## Test commands

| Command | Result |
|---|---|
| `uv run ruff format` on touched paths | pass |
| `uv run ruff check` on touched paths | pass |
| `uv run mypy` on touched packages | pass |
| `uv run pytest -m unit` | **76 passed**, 5 deselected |
| `uv run prek run --all-files` | pass |

## Leftover risks / deferred

- **OpenRouter extract adapter** — stub raises; tests use the fixture mock.
- **PDF text-layer reader** — out of scope; pipeline passes raw body + filename/mime.
- **Classer / orchestrator / machine / submitter** — not in this change.
- **`negotiate_once`** — negotiation does not mutate `line_items`; no negotiate path.
- **Fingerprint is `from\|subject`** — sample-019/020 (same sender+subject, different photos) would also classify as `duplicate` if processed in order, same as 011/012.

No git commit was made. HEAD remains `fix(supplier_loop): isolate in-memory simulator state from callers`.
