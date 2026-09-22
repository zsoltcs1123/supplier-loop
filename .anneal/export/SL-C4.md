# SL-C4 — Mock happy-path round

**Status:** done

**Path:** SL

## Kind

new_feature

## Goal

On the in-memory simulator, the loop runs a pass when inbox delta is non-empty, sends one `**RFQ**` per relevant supplier, extracts a clean quote, and calls submit_results. The submitter derives action_taken and auto_approved from stored facts plus the sent record.

## Deliverables

- Orchestrator combo trigger: inbox delta, or a due-alarm hook the machine will fill later
- Machine happy path: idle, rfq_sent, awaiting_quote, quoted, done when the classer returned no classes
- One `**RFQ**` email per relevant supplier covering every item they can fill
- Submitter verify against the in-memory sent record. Derived extract and auto_approved true only from that evidence
- Orchestrator tests: mock extract and in-memory adapter. No live provider. No live `**MCP**`

## Notes

- reminder_due, correct_once, negotiate_once, and questions wait for the mock defect path
- start_exam and request_dev_round stay with the operator
- Round state still does not store auto_approved

## Sequence

4

## Dependencies

- SL-C3: Classer

## Required by

- SL-C5: Mock defect path


## Validations



| Code | Title | Lifecycle | Change | Coverage |
| --- | --- | --- | --- | --- |
| SL-V1 | Clean quotes submit as extract | active | SL-C4 | tests/integration/orchestrator/test_happy_path.py |
