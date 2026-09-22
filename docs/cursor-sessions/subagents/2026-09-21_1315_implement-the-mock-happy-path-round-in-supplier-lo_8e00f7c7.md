# Implement the mock happy-path round in supplier-loop. Do not commit. Do not push. Do not mention Anneal, anneal entity c

- **Started:** Monday, Sep 21, 2026, 1:13 PM (UTC+2)
- **Session ID:** `8e00f7c7-5c27-4870-9a8e-8ef2566c233c`
- **Project:** `supplier-loop`
- **User turns:** 1
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/d6dcac54-a0ba-4ed5-a356-c25c512111e9/subagents/8e00f7c7-5c27-4870-9a8e-8ef2566c233c.jsonl`
- **Type:** subagent

---

## User 1

Implement the mock happy-path round in supplier-loop. Do not commit. Do not push. Do not mention Anneal, anneal entity codes, or Anneal concepts in source, tests, comments, or docs.

## Workspace

Absolute path: `/home/zs/repos/supplier-loop`
Python 3.11, uv. Package `src/supplier_loop/`. Tests `tests/`.

Read first: `PRINCIPLES.md`, `docs/SEED.md`, `docs/ARCHITECTURE.md`, `docs/spec/ESCALATION_RULES.md`, `docs/spec/RFQ_FORMAT.md`, `DEVELOPING.md`, `.cursor/rules/python.mdc`, `.cursor/rules/python-testing.mdc`.

Reuse existing modules. Do not duplicate models.

Already landed:
- Simulator protocol + `InMemorySimulator` (`src/supplier_loop/simulator/`) — `push_inbox`, `sent_emails`, `last_submission`, `advance_clock`
- Round state models + `RoundStore` + `snapshot_world` (`src/supplier_loop/round_state/`)
- Operational log (`src/supplier_loop/operational_log/`)
- Mail kind + quote pipeline (`process_inbound_mail`, `FixtureExtractor`)
- Classer `required_classes(...)` → `frozenset[int]`
- Progress printer `emit_progress`

`QuoteRecord` / `SupplierFacts` already exist. Round state MUST NOT store `action_taken` or `auto_approved`.

## Outcome

On the in-memory simulator, the loop runs a pass when inbox delta is non-empty (or a due-alarm hook that is empty for now), sends one RFQ per relevant supplier, extracts a clean quote, and calls `submit_results`. The submitter derives `action_taken` and `auto_approved` from stored facts plus the sent record.

### Deliverables

1. **Orchestrator combo trigger.** Run the rest of a pass when:
   - inbox delta is non-empty (new email ids vs `dedup.email_ids`), OR
   - a due-alarm hook returns something (machine fills this later; for this change return empty), OR
   - relevant suppliers are still `idle` and need their first RFQ (empty inbox must not skip the initial RFQ send).
   If none of those, return without ingesting/acting.
   `start_exam` and `request_dev_round` stay with the operator. Not part of a poll pass.

2. **Machine happy path only.** Phases: `idle` → send RFQ → `rfq_sent` / `awaiting_quote` → inbound quote → `quoted` → classer empty → `done`.
   Do NOT implement `reminder_due`, `correct_once`, `negotiate_once`, questions, or escalation sends. Those wait for a later defect-path change. Leave a due-alarm hook the machine can fill later.

3. **One RFQ email per relevant supplier.** Relevant = directory entry whose `material_ids` intersect the BOM. One email covers every BOM item that supplier can fill. No second RFQ to the same supplier. No RFQ to a supplier who carries zero BOM lines. Record outbound ids on `SupplierFacts`.

4. **Submitter.** After acts, re-read the simulator sent record and inbox. Do not verify from process memory of the send call. Derive:
   - `action_taken`: precedence `escalated` > `answered_question`/`reminded` > `extract`. Happy path: `extract`.
   - `auto_approved`: true only from evidence that this supplier was not escalated (no `[REF:<supplier_id>]` in the sent record) and classer required no classes.
   If classer required classes, this change should not pretend auto_approved; happy-path tests use clean quotes so classer returns empty.
   Submit payload: as-sent qty/unit_price/payment_terms/validity_days; recomputed `total` / `grand_total` from the Quote record. Do not invent lines. Include every relevant supplier who reached `done` with a quote.
   Round-state files must still reject / omit `action_taken` and `auto_approved`.

5. **Orchestrator tests** with `FixtureExtractor` and `InMemorySimulator`. No live provider. No live MCP.

### Acceptance scenarios (must pass; encode as tests against the running in-memory loop + disk files)

These are the change's validations. Implement them as integration tests that actually run the loop and inspect simulator + files:

A. Load an in-memory round where every relevant supplier returns a clean quote. Run the loop until it calls `submit_results`. The in-memory sent record has one RFQ per supplier who carries a BOM line, and no second RFQ to the same supplier. Each `submit_results` entry has `action_taken` `extract` and `auto_approved` true. Round-state files contain no `action_taken` and no `auto_approved`.

B. Start a second in-memory round (new `round_id`, wipe mutable round state, snapshot again). Mutable round-state files no longer hold the first round's Quote records. The operational log still has the first round's lines.

Cover at least two relevant suppliers plus one irrelevant supplier (carries no BOM line) so RFQ targeting is proven.

## Design notes

- Suggested modules: `src/supplier_loop/orchestrator/`, `src/supplier_loop/machine/` (happy path only), `src/supplier_loop/submitter/`. Keep them thin.
- Classer is the only path that names required classes. Machine writes phase + outbound facts. Pipeline writes Quote record. Submitter is the only path that may set `auto_approved` true, and only from sent-record evidence.
- Persist `injection_suspected` on `SupplierFacts` if you need it after extract (do not put it on QuoteRecord). Happy-path quotes use `injection_suspected=False`.
- Submitter needs a sent-record read. `InMemorySimulator.sent_emails()` exists as a test helper. If business logic must read sent mail, add a narrow method on the `Simulator` protocol (e.g. `list_sent()`) and implement it on the in-memory adapter. Do not have the submitter trust an in-memory list the orchestrator kept beside the adapter.
- Inbox delta: mark email ids in `dedup.email_ids` after processing. `process_inbound_mail` already writes quote fingerprints.
- For tests: send RFQs on first pass; `push_inbox` quote-shaped messages; `FixtureExtractor` returns a clean `ExtractResult` matching BOM qty/terms/validity and unit prices at or below last-accepted * (1 + ceiling%). Then run until submit.
- Quote-shaped mail: classifier needs ≥2 priced item lines OR attachments plus quote/offer words. Easiest: body with two `qty N ... USD` lines, or subject containing "quote" plus an attachment id (extractor still keyed by email id).
- Operational log is append-only JSONL via `OperationalLog.append`. Use it during the round so scenario B can prove survival across wipe.
- Do not change `QuoteRecord` extra-forbid behavior.
- Surgical. No comments. No docstrings except public API. Absolute imports. Type hints. Prefer functions. No `monkeypatch.setattr` on first-party modules. Prefer real in-memory adapter over mocks of our own code.
- Tests: `@pytest.mark.unit` for pure machine/submitter helpers; `@pytest.mark.integration` for the disk-backed loop scenarios (A/B). Names `test_<subject>_<expected_behavior>_when_<condition>`.
- File size ≤ 500 lines per source file.

## Existing types you will wire

```
process_inbound_mail(message, supplier=, rfq=, dedup=, extractor=, attachments=) -> MailKind
required_classes(quote, rfq, supplier_id=, injection_suspected=, own_quote_history=) -> frozenset[int]
FixtureExtractor(results: Mapping[email_id, ExtractResult])
ExtractResult(line_items, payment_terms, validity_days, grand_total, injection_suspected)
SubmitEntry, SubmitLineItem in simulator/port.py
RoundStore.save/load/wipe, snapshot_world
```

Match quote lines to BOM. Clean quote = all carried BOM lines present, qty match, terms match, validity >= required, unit price within ceiling, no injection, empty own_quote_history.

## Verify

1. ruff format/check on touched paths
2. mypy on touched packages
3. `uv run pytest` (unit + integration)
4. `uv run prek run --all-files`

Fix failures you introduce.

## Return to parent

Single report: modules and phase transitions, file list, how trigger/submitter work, test commands + results, leftover risks (title + 1 line). Confirm no git commit. Do not implement defect-path behavior. Do not use the anneal CLI.

## Assistant

Me read docs and poke existing code first — then wire happy-path orchestrator, machine, submitter.

[REDACTED]
[tool: UpdateCurrentStep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Glob]
[tool: Glob]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Me build orchestrator, machine, submitter now — wire simulator `list_sent` and tests after.

[REDACTED]
[tool: UpdateCurrentStep]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]

## Assistant

Me clean up `run.py` — kill sloppy typing and inline imports.

[REDACTED]
[tool: Write]
[tool: Write]

## Assistant

[REDACTED]
[tool: StrReplace]

## Assistant

Next up: unit tests and integration scenarios A and B.

[REDACTED]
[tool: Write]
[tool: Write]
[tool: Write]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]
[tool: Shell]

## Assistant

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Read]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: UpdateCurrentStep]

## Assistant

## Report for parent

### Modules and phase transitions

**Orchestrator** (`src/supplier_loop/orchestrator/`)
- `trigger.py` — combo trigger: inbox delta, `due_alarms()` (empty hook), idle relevant suppliers need first RFQ
- `relevance.py` — BOM intersection, supplier lookup, RFQ line selection
- `run.py` — `run_pass()` / `run_until_submit()`: refresh inbox → trigger → ingest → act → submit → persist

**Machine** (`src/supplier_loop/machine/`) — happy path only
- `due.py` — `due_alarms()` returns `[]` (machine fill later)
- `happy.py` — RFQ send, quote receipt, classer apply

Phase flow:
```
idle → (send RFQ) → awaiting_quote → (quote ingest) → quoted → (classer empty) → done
```

**Submitter** (`src/supplier_loop/submitter/submit.py`)
- Re-reads `simulator.list_sent()` (new protocol method)
- Derives `action_taken` / `auto_approved`; builds payload from `QuoteRecord`

### Files touched

| Area | Files |
|------|-------|
| New | `orchestrator/{__init__,trigger,relevance,run}.py`, `machine/{__init__,due,happy}.py`, `submitter/{__init__,submit}.py` |
| Tests | `tests/unit/orchestrator/test_trigger.py`, `tests/unit/submitter/test_submit.py`, `tests/integration/orchestrator/test_happy_path.py` |
| Modified | `simulator/port.py` (`SentEmailRecord`, `list_sent()`), `simulator/memory.py`, `round_state/models.py` (`injection_suspected`), `quote_pipeline/pipeline.py` |

### How trigger works

`run_pass` refresh inbox from simulator first, then `should_run_pass()`:
1. `due_alarms(state)` non-empty → run
2. Any inbox id not in `dedup.email_ids` → run
3. Any **relevant** supplier (`material_ids` ∩ BOM) still `idle` → run (empty inbox still sends first RFQ)
4. Else → return without ingest/act/persist

### How submitter works

After all relevant suppliers `done` with quotes:
- `build_submit_payload()` calls `simulator.list_sent()` (not process memory)
- `action_taken`: `escalated` if `[REF:<id>]` mail to approver; else `answered_question` / `reminded` / `extract`
- `auto_approved`: `true` only when no escalation mail in sent record AND `escalation_classes` empty
- Payload: as-sent qty/unit_price/terms/validity; `total`/`grand_total` from recomputed Quote record
- Round-state JSON still omits `action_taken` / `auto_approved`

### Test commands + results

```bash
uv run pytest                                    # 109 passed
uv run pytest -m integration                     # includes scenarios A/B
uv run ruff check/format <touched paths>         # passed
uv run mypy <touched packages>                   # passed
uv run prek run --all-files                      # passed
```

**Scenario A** (`test_orchestrator_submits_clean_quotes_when_all_relevant_suppliers_reply`): p01+p02 get one RFQ each, p03 (WOOD-PLANK) gets none; submit has `extract` + `auto_approved: true`; round.json has no action fields.

**Scenario B** (`test_orchestrator_wipes_quotes_but_keeps_log_when_new_round_starts`): wipe + new `round_id` clears quotes; operational log keeps round-1 lines.

### Leftover risks

| Risk | Note |
|------|------|
| No defect paths | `reminder_due`, `correct_once`, `negotiate_once`, escalation sends not implemented |
| `due_alarms` stub | Always empty; machine must fill for reminders/validity/quiet-margin |
| `run_until_submit` | Uses `InMemorySimulator.last_submission()`; live MCP adapter needs equivalent |
| Single-pass ordering | Ingest before RFQ send same pass; fine for happy path, may need tweak for concurrent inbound |

### Git

No commit. No push.

[REDACTED]
