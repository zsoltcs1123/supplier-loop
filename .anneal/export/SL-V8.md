# SL-V8 — No escalation before a quote is stored

**Status:** active

**Path:** SL

## Scenarios

- Load an in-memory round. Send RFQs. Advance sim time with an empty inbox. The sent record has supplier RFQs and no mail to approver@`sim.local`. No [`**REF**`:<supplier_id>] subject exists until that supplier has a stored Quote record.

## Coverage

tests/integration/orchestrator/`test_exam_readiness.py`

## Lifecycle

active
