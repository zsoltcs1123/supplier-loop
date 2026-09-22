# Supplier Loop

**Status:** live

0 sub-projects, 0 open changes, 9 validations, 3 knowledge, 0 milestones, 3 docs, 0 followups, 0 bugs, 0 ideas

**Path:** SL

Supplier Loop is an unattended quoting loop against the LeadFlow Automation supplier simulator. The loop reads each RFQ, emails the suppliers who can fill it, extracts quotes, validates them in code, escalates when docs/spec/ESCALATION_RULES.md requires it, and calls submit_results before the deadline.

This is a timed evaluation, not a product. Extract is the only model step. Code owns every later decision. The model never acts.

Out of scope: a ReAct agent that makes every decision; LangGraph or another heavy agent framework as the default; invented extraction values; an escalation that says the loop could not read the artifact; a second reminder or a second correction request; parallel development rounds.

## Docs

- architecture — docs/ARCHITECTURE.md
- brief — docs/spec/CHALLENGE-BRIEF-SUPPLIER-LOOP.md
- vision — docs/SEED.md

## Capabilities

- Combo trigger on inbox delta or a machine due-alarm
- Simulator seam: MCP adapter at runtime, in-memory adapter in tests
- Mail kind classifier; only quote uses Extract
- Extract port, extra fields forbidden
- Quote pipeline as the only writer of the Quote record
- Classer returns required classes only
- Lifecycle machine: phases, correct_once, negotiate_once, due alarms
- Round state wiped on round change; operational log never truncates
- Submitter derives action_taken and auto_approved from facts plus the sent record

## Changes

| Code | Title | Status |
| --- | --- | --- |
| SL-C1 | In-memory simulator, round state, and operational log | done |
| SL-C2 | Mail kind classifier and fixture quote pipeline | done |
| SL-C3 | Classer | done |
| SL-C4 | Mock happy-path round | done |
| SL-C5 | Mock defect path | done |
| SL-C6 | First live development round | done |
| SL-C7 | OpenRouter extract for PDFs and photos | done |
| SL-C8 | Unattended live round | done |
| SL-C9 | Exam readiness | done |
| SL-C10 | Operator proposal pack after a development round | done |

## Validations

| Code | Title | Lifecycle | Change | Coverage |
| --- | --- | --- | --- | --- |
| SL-V1 | Clean quotes submit as extract | active | SL-C4 | tests/integration/orchestrator/test_happy_path.py |
| SL-V2 | Defects act once and submit from evidence | active | SL-C5 | tests/integration/orchestrator/test_defect_path.py |
| SL-V3 | Live development round reaches submit_results | active | SL-C6 | unclaimed |
| SL-V4 | Unattended live round completes | active | SL-C8 | unclaimed |
| SL-V5 | Embedded instructions escalate from supplier text | active | SL-C9 | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V6 | Unreadable quote is not a terms discrepancy | active | SL-C9 | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V7 | Revised re-escalation matches the quote on file | active | SL-C9 | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V8 | No escalation before a quote is stored | active | SL-C9 | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V9 | Proposal pack dumps a finished round without spending the extract key | active | SL-C10 | src/supplier_loop/cli.py, src/supplier_loop/propose.py, src/supplier_loop/operational_log/log.py, docs/proposals/PROMPT.md |

## Knowledge

- SL-K1 — Live list_inbox is inbound-only and timestamps are sim_time seconds (active)
- SL-K2 — openai/gpt-4o-mini misreads the Alsayed screenshot fixture (active)
- SL-K3 — Proposal pack is operator-only and never spends the extract key (active)
