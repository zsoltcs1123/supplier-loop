# SL-V6 — Unreadable quote is not a terms discrepancy

**Status:** active

**Path:** SL

## Scenarios

- Load an in-memory round. First extract of a quote mail returns no line items, payment_terms empty, validity_days 0. The sent record has no [`**REF**`:<supplier_id>] mail for class 3 or class 4. The supplier is not submitted with invented empty terms as a discrepancy.
- On a later pass, extract of that same mail returns real line items and matching terms. The loop stores those lines. No class 3 or class 4 mail was sent in between.

## Coverage

tests/integration/orchestrator/`test_exam_readiness.py`

## Lifecycle

active
