# SL-C9 — Exam readiness

**Status:** done

**Path:** SL

## Kind

feature_update

## Goal

The loop escalates embedded supplier instructions even when Extract misses the flag, and it does not treat an unreadable quote as a terms or validity discrepancy. After a correction, the re-escalation describes the quote now on file. The loop never calls start_exam. Only the operator does, out of band; resume-dev then runs against that round. The submission includes an honest self-evaluation.

## Deliverables

- Code scan of supplier body and `**PDF**` text may set injection_suspected only. Class 7 mail quotes the trapped phrase. Fixture: docs/fixtures/sample_traffic/emails/014_p03_re-rfq-rfq-003-request-for-`quote.json`
- Classer omits classes 1, 3, and 4 when the quote has no line items. The unattended loop retries extract while lines are empty
- Re-escalation after correction describes the quote now on file. It does not claim a mismatch the revised document no longer has
- No `**CLI**` command, poll pass, helper, or test harness calls start_exam. After the operator starts the exam by hand, resume-dev runs the loop against that round. `**README**` states only the operator calls start_exam
- One-page self-evaluation with measured live-round numbers and known weaknesses. `**README**` names `**PYTHONIOENCODING**`=utf-8 and the resume-dev exam path

## Notes

- Converts the injection-scan idea. The scan sets the flag only. It does not pick an action from prose
- start_exam is operator-only under every circumstance. The repo must not grow a start_exam caller
- Submit-echo warning retry, as-sent prior-quote citation in class 6, and fuzzy description match stay out of this change

## Sequence

9

## Dependencies

- SL-C8: Unattended live round


## Validations



| Code | Title | Lifecycle | Change | Coverage |
| --- | --- | --- | --- | --- |
| SL-V5 | Embedded instructions escalate from supplier text | active | SL-C9 | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V6 | Unreadable quote is not a terms discrepancy | active | SL-C9 | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V7 | Revised re-escalation matches the quote on file | active | SL-C9 | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V8 | No escalation before a quote is stored | active | SL-C9 | tests/integration/orchestrator/test_exam_readiness.py |
