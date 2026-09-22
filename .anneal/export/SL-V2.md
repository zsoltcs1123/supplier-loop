# SL-V2 — Defects act once and submit from evidence

**Status:** active

**Path:** SL

## Scenarios

- Advance sim time past reminder_due with no quote. The sent record has one reminder to that supplier and no second reminder. submit_results for that supplier has action_taken reminded unless a later escalation outranks it.
- Inbox contains a supplier question and no quote table. Extract is not called. The sent record has one answer taken from the `**RFQ**`.
- Approver rejects a missing-line class. The machine runs correct_once once. Round state's Quote record has revised_as_sent. The sent record has a new [`**REF**`:<supplier_id>] mail. There is no second correction request.
- Price is over the ceiling. The machine runs negotiate_once once. The Quote record as_sent line items are unchanged. The sent record has a body with a plain-number target total, then a class 6 [`**REF**`:<supplier_id>] mail. submit_results has action_taken escalated and auto_approved false until the approver approves.
- A quote has injection_suspected true. The classer returns class 7. The sent record has a matching [`**REF**`:<supplier_id>] mail. After the submitter reads that record, auto_approved is false.

## Coverage

tests/integration/orchestrator/`test_defect_path.py`

## Lifecycle

active
