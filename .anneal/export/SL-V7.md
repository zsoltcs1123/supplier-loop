# SL-V7 — Revised re-escalation matches the quote on file

**Status:** active

**Path:** SL

## Scenarios

- Approver rejects class 3. The machine sends one correction. The supplier returns a revised quote whose payment_terms match the `**RFQ**`. The next [`**REF**`:<supplier_id>] mail describes the quote now on file. That body does not say payment terms differ when they match.

## Coverage

tests/integration/orchestrator/`test_exam_readiness.py`

## Lifecycle

active
