# Implement the mock defect path in supplier-loop. Do not commit. Do not push. Do not mention Anneal, anneal entity codes,

- **Started:** Monday, Sep 21, 2026, 1:17 PM (UTC+2)
- **Session ID:** `86b083da-8919-44c8-9b2a-05ae0d255432`
- **Project:** `supplier-loop`
- **User turns:** 1
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/d6dcac54-a0ba-4ed5-a356-c25c512111e9/subagents/86b083da-8919-44c8-9b2a-05ae0d255432.jsonl`
- **Type:** subagent

---

## User 1

Implement the mock defect path in supplier-loop. Do not commit. Do not push. Do not mention Anneal, anneal entity codes, or Anneal concepts in source, tests, comments, or docs.

## Workspace

Absolute path: `/home/zs/repos/supplier-loop`
Python 3.11, uv. Package `src/supplier_loop/`. Tests `tests/`.

Read first: `PRINCIPLES.md`, `docs/SEED.md`, `docs/ARCHITECTURE.md`, `docs/spec/ESCALATION_RULES.md`, `docs/spec/RFQ_FORMAT.md`, `docs/spec/FAQ.md` (esp. 15–16), `DEVELOPING.md`, `.cursor/rules/python.mdc`, `.cursor/rules/python-testing.mdc`.

Happy-path already works. Extend it. Do not rewrite the orchestrator from scratch. Do not re-implement the classer. Do not add live MCP or OpenRouter.

## Existing wiring (read these)

- `src/supplier_loop/orchestrator/run.py` — `run_pass` / `run_until_submit`: refresh inbox → trigger → ingest → `send_pending_rfqs` → `advance_quoted_suppliers` → submit if ready
- `src/supplier_loop/machine/happy.py` — RFQ send, `mark_quote_received`, classer apply; empty classes → `done`. Currently does **not** send `[REF:]` mails when classes are non-empty (quoted stays quoted).
- `src/supplier_loop/machine/due.py` — `due_alarms()` always `[]`
- `src/supplier_loop/submitter/submit.py` — derives action from sent record + facts. `round_ready_to_submit` requires every relevant supplier `done` with a quote. You **must** change that: a reminded silent supplier with no quote is still a submit entry (`action_taken=reminded`, do not invent line items).
- `src/supplier_loop/quote_pipeline/pipeline.py` — extract only for kind `quote`
- `src/supplier_loop/mail_kind/classify.py` — kinds include question, negotiation_reply, duplicate, approver_ruling
- `InMemorySimulator.advance_clock`, `push_inbox`, `list_sent`, `last_submission`
- `SupplierFacts`: `correction_used`, `reminder_sim_time`, `question_answered`, `approver_rulings`, `own_quote_history`, `escalation_classes`, `injection_suspected`

## Outcome

On the in-memory simulator: remind once on `reminder_due`, answer a question without extract, request one correction, negotiate once, send every required class. Submitter derives strongest `action_taken` from facts plus sent record.

### Deliverables

1. **correct_once** — for classes 1 (missing line), 2 (quantity), 3 (payment terms), 4 (validity). Concrete correction request to the supplier. One per supplier (`correction_used`). Revised inbound quote is extracted into `QuoteRecord.revised_as_sent` (as-sent original stays). Classer runs again on the revised document. Machine escalates again. A second correction is a no-op.

2. **negotiate_once** — for class 5 (price over ceiling). Not a correction. Body states a **target total as a plain number** (FAQ 15, e.g. a number the supplier can parse; do not merely restate their price). Original `as_sent.line_items` stay frozen. Record own quote history so classer returns 6. Outcome always escalates as class 6. One exchange per round.

3. **Due alarms** — fill `due_alarms()`:
   - `reminder_due` when a relevant supplier is `awaiting_quote` (or `rfq_sent`) past a named constant threshold and `reminder_sim_time` is None.
   - `validity_alarm` when a quoted supplier’s validity is near expiry (named constant). Bind values in tests. Do **not** pretend these are exam-tuned. Reminder threshold / quiet margin / poll interval / iteration cap stay open for a later change; just pick testable constants.
   One reminder only. Second reminder is out of scope (no-op if already reminded).

4. **Skip extract** for questions, number-only negotiation replies, duplicates, approver rulings. Pipeline already skips non-quote; orchestrator/machine must **act** on those kinds:
   - question → one answer from RFQ facts; `question_answered=True`
   - negotiation_reply → do not rewrite line_items; complete negotiate_once / class 6 escalate
   - duplicate → no second RFQ, no extra extract
   - approver ruling → pick `correct_once` (classes 1–4) or `negotiate_once` (price) by class, never by the model. Approver address is `approver@sim.local`.

5. **Several required classes → several `[REF:<supplier_id>]` mails in one pass.** One class per email, concrete claim (quote vs RFQ/history). Send every required class. Content discrepancy (1–4, 7) outranks negotiation. Class 5 is negotiated then escalated as 6; still send class 7 / 1–4 as their own mails.

6. **Orchestrator tests** on in-memory adapter + fixture extract. No live provider. No live MCP. **Do not re-assert classer unit tests.** This change does not re-assert classes as submit flags. Injection test: classer class 7 (you may call `required_classes` once to confirm the flag path, but the orchestrator test asserts the **mail** and derived `auto_approved false`).

### Acceptance scenarios (must pass as integration tests against the running in-memory loop)

Implement **all five** as tests that run the loop and inspect simulator sent record + round state:

A. Advance sim time past `reminder_due` with no quote. Sent record has **one** reminder to that supplier and no second reminder. `submit_results` for that supplier has `action_taken` `reminded` unless a later escalation outranks it. Do not invent line items for a silent supplier.

B. Inbox contains a supplier question and no quote table. Extract is **not** called (`FixtureExtractor.requests` empty or no extract for that id). Sent record has one answer taken from the RFQ.

C. Approver rejects a missing-line class. Sequence: missing-line quote → escalate class 1 `[REF:]` → push approver rejection → `correct_once` once → push revised quote → `revised_as_sent` set → classer again → new `[REF:]` mail. No second correction request.

D. Price over the ceiling. `negotiate_once` once. `as_sent.line_items` unchanged. Sent record has a body with a plain-number target total, then a class 6 `[REF:<supplier_id>]` mail. `submit_results` has `action_taken` `escalated` and `auto_approved` false until the approver approves.

E. Quote has `injection_suspected=True`. Classer returns class 7. Sent record has matching `[REF:<supplier_id>]` mail. After submitter reads that record, `auto_approved` is false.

Happy-path tests in `tests/integration/orchestrator/test_happy_path.py` must still pass.

## Behavior details

**Escalation mail:** to `assignment.approver_email`, subject contains `[REF:<supplier_id>]`, body names the class and the concrete discrepancy. No `auto_approved` true while required classes are open or while a matching `[REF:]` mail exists.

**Submitter / ready-to-submit:**
- Precedence already: escalated > answered_question / reminded > extract.
- If classer required an escalation, sent record must contain matching `[REF:<supplier_id>]`. If that mail is missing, do **not** submit a clean extract/auto_approved result.
- Silent-after-reminder supplier: include in payload with `action_taken=reminded`, empty `line_items`, no invented prices. Schema still needs payment_terms/validity_days/grand_total — use empty string / 0 / 0.0, not fake quote data.
- `auto_approved` true only from evidence: no `[REF:]` for that supplier and no required classes.
- Round state still does not store `action_taken` / `auto_approved`.

**Phases:** do not move `quoted` → `done` while required classes are still open. After required `[REF:]` mails are sent, phase `escalated`. After reminder, stay awaiting (or a reminded wait) until quote or round submit of remaining suppliers. For scenario A, round can submit the reminded supplier without a quote.

**Machine vs classer:** classer only returns class numbers. Machine sends mail and updates facts. Submitter only derives flags from evidence.

**Constants:** put reminder threshold and validity margin in one small module (named constants). Tests advance `InMemorySimulator.advance_clock` past them.

**File size:** source files ≤ 500 lines. Split machine into focused modules (`due.py`, `correct.py`, `negotiate.py`, `escalate.py`, etc.) rather than growing `happy.py` forever.

**Orchestrator ingest:** today it only `mark_quote_received` on quote. Extend to dispatch question / ruling / negotiation_reply / duplicate. Keep extract only for quote.

**revised_as_sent:** pipeline currently always writes `supplier.quote = build_quote_record(...)` which replaces the whole record. For a correction follow-up quote, keep original `as_sent` and set `revised_as_sent`. Classer already uses `revised_as_sent` when present. You will need a pipeline/orchestrator path for "this is a revised quote after correct_once" — e.g. if `correction_used` and a quote already exists, fill `revised_as_sent` instead of replacing `as_sent`.

**Target total for negotiate:** last-accepted prices * qty within ceiling is a reasonable number; must appear as a plain number in the body.

Surgical. No comments. No docstrings except public API. Absolute imports. Type hints. No first-party `monkeypatch.setattr`. Prefer real in-memory adapter. Test names `test_<subject>_<expected_behavior>_when_<condition>`. `@pytest.mark.integration` for the five scenarios; unit tests for due-alarm helpers / one-correction no-op / one-reminder no-op.

Do not implement live development round, MCP adapter, OpenRouter, README one-command, WORKLOG, loop contract.

## Verify

1. ruff format/check on touched paths
2. mypy on touched packages
3. `uv run pytest` (unit + integration, including existing happy-path)
4. `uv run prek run --all-files`

Fix failures you introduce.

## Return to parent

Single report: what landed (alarms, correct, negotiate, escalate), file list, how submitter treats silent/reminded suppliers, test commands + results for scenarios A–E, leftover risks. Confirm no git commit. No anneal CLI.

## Assistant

Me read docs and existing wiring first, then implement mock defect path surgical.

[REDACTED]
[tool: UpdateCurrentStep]
[tool: Read]
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
[tool: Read]

## Assistant

[REDACTED]
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
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Me implement machine modules, orchestrator wiring, submitter changes, then tests.

[REDACTED]
[tool: UpdateCurrentStep]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Write]
[tool: Write]

## Assistant

[REDACTED]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: Write]

## Assistant

[REDACTED]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: StrReplace]
[tool: StrReplace]
[tool: Write]

## Assistant

[REDACTED]
[tool: Write]
[tool: Write]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Write]
[tool: Write]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Grep]

## Assistant

[REDACTED]
[tool: Write]
[tool: Shell]

## Assistant

Test bodies need two priced lines so mail classifier sees quote, not question. Me fix that.

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

After revised quote, me add re-escalation when approver rejected — classer alone not enough.

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

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

## Assistant

[REDACTED]
[tool: Shell]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Read]

## Assistant

[REDACTED]
[tool: StrReplace]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Read]

## Assistant

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Shell]
[tool: UpdateCurrentStep]

## Assistant

## Report: mock defect path

### What landed

**Due alarms** (`machine/constants.py`, `machine/due.py`)
- `REMINDER_THRESHOLD_SIM_SECONDS = 86400` (1 sim-day)
- `VALIDITY_ALARM_MARGIN_DAYS = 2.0`
- `reminder_due`: supplier in `awaiting_quote`/`rfq_sent`, past threshold, `reminder_sim_time` still None
- `validity_alarm`: quoted supplier quote expiry within margin

**Remind once** (`machine/remind.py`)
- One reminder email per supplier; second pass no-op

**Escalate** (`machine/escalate.py`)
- One `[REF:<supplier_id>]` mail per class (1–4, 7, 6; not 5)
- Concrete body per class; revised correction uses `Class N (revised):` marker

**Correct once** (`machine/correct.py`, `machine/ruling.py`)
- Classes 1–4: concrete correction request; `correction_used` blocks second
- Approver rejection → path by class number from body / escalation state
- `last_rejection_class` drives post-revision re-escalation

**Negotiate once** (`machine/negotiate.py`)
- Class 5 → counter-offer with plain-number target total (ceiling-priced sum)
- `own_quote_history` set → classer adds 6 → class 6 `[REF:]` mail
- `as_sent.line_items` stay frozen

**Orchestrator ingest** (`orchestrator/run.py`)
- Dispatches: quote, question, negotiation_reply, duplicate, approver_ruling
- Extract only on quote; `revised_as_sent` when `correction_used` and quote exists

**Machine advance** (`machine/advance.py`)
- Classer → negotiate (5) → escalate REF mails → phase `escalated` or `done`

**Submitter** (`submitter/submit.py`)
- Ready when: `done`+quote, `escalated`+quote, or reminded with no quote
- Silent/reminded: `action_taken=reminded`, empty `line_items`, `payment_terms=""`, `validity_days=0`, `grand_total=0.0`, `auto_approved=false`
- `escalated` beats `reminded`/`answered_question`; `auto_approved` false when `[REF:]` mail or open escalation classes

### Files touched

| Area | Files |
|------|-------|
| New | `machine/constants.py`, `advance.py`, `answer.py`, `correct.py`, `escalate.py`, `negotiate.py`, `remind.py`, `ruling.py` |
| Modified | `machine/due.py`, `happy.py`, `__init__.py`, `orchestrator/run.py`, `__init__.py`, `quote_pipeline/pipeline.py`, `round_state/models.py`, `submitter/submit.py` |
| Tests | `tests/integration/orchestrator/test_defect_path.py`, `tests/unit/machine/test_due.py` |

### Test commands + results

```bash
uv run pytest tests/integration/orchestrator/test_defect_path.py -m integration -q
uv run pytest tests/integration/orchestrator/test_happy_path.py -q
uv run pytest tests/unit/machine/test_due.py -m unit -q
uv run pytest -q
uv run prek run --all-files
```

**120 passed**, prek green.

| Scenario | Test | Result |
|----------|------|--------|
| A Reminder | `test_orchestrator_sends_one_reminder_when_supplier_stays_silent` | PASS — 1 reminder, `action_taken=reminded`, no invented line items |
| B Question | `test_orchestrator_answers_question_without_extract_when_no_quote_table` | PASS — `extractor.requests == []`, answer from RFQ facts |
| C Correction | `test_orchestrator_corrects_once_after_approver_rejects_missing_line` | PASS — class 1 REF → reject → 1 correction → `revised_as_sent` → 2nd REF |
| D Negotiate | `test_orchestrator_negotiates_price_then_escalates_class_six` | PASS — `4,200.00` target, frozen lines, class 6 REF, `escalated`/`auto_approved=false` |
| E Injection | `test_orchestrator_escalates_injection_and_sets_auto_approved_false` | PASS — class 7 REF, `auto_approved=false` |

Happy-path regression: `test_happy_path_still_submits_after_defect_wiring` — PASS.

### Leftover risks

- **Validity alarm** wired and unit-tested; not exercised in A–E integration scenarios yet
- **Post-correction re-escalation** re-sends same class with `(revised)` marker even when revised quote is clean — matches spec intent but body may list empty missing lines on a fixed quote
- **Quiet margin / round-done** not implemented (out of scope)
- **Second reminder** intentionally no-op only; no explicit log noise guard beyond `reminder_sim_time`
- Circular import fixed by trimming `orchestrator/__init__.py`; callers must import `run_pass` from `orchestrator.run` directly

### Git

**No commit. No push.** Working tree has uncommitted changes only.

[REDACTED]
