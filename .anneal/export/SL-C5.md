# SL-C5 — Mock defect path

**Status:** done

**Path:** SL

## Kind

new_feature

## Goal

On the in-memory simulator, the loop reminds once on reminder_due, answers a question without extract, requests one correction, negotiates once, and sends every required class. The submitter derives the strongest action_taken from facts plus the sent record.

## Deliverables

- Machine correct_once: revised Quote record replaces as-sent, classer runs again, one correction per supplier
- Machine negotiate_once: original Quote record stays frozen, outcome is class 6, plain-number target total
- Due alarms: reminder_due and validity_alarm. Approver rejection picks correct_once or negotiate_once by class
- Questions, number-only negotiation replies, duplicates, and approver rulings skip extract
- Several required classes mean several [`**REF**`:<supplier_id>] mails in one pass
- Orchestrator tests on the in-memory adapter. Injection test: classer class 7, matching escalation mail, derived auto_approved false

## Notes

- Reminder threshold, quiet margin, poll interval, and iteration cap stay open until the unattended live round
- A second reminder or a second correction is out of scope
- Classer tests stay on C3. This change does not re-assert classes as submit flags

## Sequence

5

## Dependencies

- SL-C4: Mock happy-path round

## Required by

- SL-C6: First live development round


## Validations



| Code | Title | Lifecycle | Change | Coverage |
| --- | --- | --- | --- | --- |
| SL-V2 | Defects act once and submit from evidence | active | SL-C5 | tests/integration/orchestrator/test_defect_path.py |

## Followups



| Code | Title | Status | Change | Converted To |
| --- | --- | --- | --- | --- |
| SL-F2 | Re-escalation after correction must describe the quote now on file | done | SL-C5 | — |
