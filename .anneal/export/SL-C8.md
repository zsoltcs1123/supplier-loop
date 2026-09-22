# SL-C8 — Unattended live round

**Status:** done

**Path:** SL

## Kind

feature_update

## Goal

The loop completes a live development round without you driving individual acts. Reminder threshold, inbox-quiet margin, poll interval, and iteration cap are set from that run. The loop contract is filled. `**README**` is one command.

## Deliverables

- One unattended live development round from `**RFQ**` send through submit_results
- Chosen values for reminder threshold in sim-days, inbox-quiet margin, poll interval, and iteration cap
- Loop contract filled from docs/spec/`**LOOP_CONTRACT_TEMPLATE**`.md
- `**README**` one-command run on Python 3.11

## Notes

- Clock policy stays on the machine. This change binds the open numbers from docs/`**SEED**`.md
- start_exam stays operator-owned and is not part of this change
- The backup injection heuristic stays the idea, not this change

## Sequence

8

## Dependencies

- SL-C7: OpenRouter extract for PDFs and photos

## Required by

- SL-C9: Exam readiness


## Validations



| Code | Title | Lifecycle | Change | Coverage |
| --- | --- | --- | --- | --- |
| SL-V4 | Unattended live round completes | active | SL-C8 | unclaimed |

## Followups



| Code | Title | Status | Change | Converted To |
| --- | --- | --- | --- | --- |
| SL-F8 | Resend the concrete claim when the approver asks for specifics | done | SL-C8 | — |
