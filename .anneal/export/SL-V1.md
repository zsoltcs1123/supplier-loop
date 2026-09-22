# SL-V1 — Clean quotes submit as extract

**Status:** active

**Path:** SL

## Scenarios

- Load an in-memory round where every relevant supplier returns a clean quote. Run the loop until it calls submit_results. The in-memory sent record has one `**RFQ**` per supplier who carries a `**BOM**` line, and no second `**RFQ**` to the same supplier. Each submit_results entry has action_taken extract and auto_approved true. Round-state files contain no action_taken and no auto_approved.
- Start a second in-memory round. Mutable round-state files no longer hold the first round*'s Quote records. The operational log still has the first round'*s lines.

## Coverage

tests/integration/orchestrator/`test_happy_path.py`

## Lifecycle

active
