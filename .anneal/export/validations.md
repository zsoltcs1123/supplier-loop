# Validations

## SL — Supplier Loop

| Code | Title | Change | Status | Coverage |
| --- | --- | --- | --- | --- |
| SL-V1 | Clean quotes submit as extract | SL-C4 | active | tests/integration/orchestrator/test_happy_path.py |
| SL-V2 | Defects act once and submit from evidence | SL-C5 | active | tests/integration/orchestrator/test_defect_path.py |
| SL-V3 | Live development round reaches submit_results | SL-C6 | active | unclaimed |
| SL-V4 | Unattended live round completes | SL-C8 | active | unclaimed |
| SL-V5 | Embedded instructions escalate from supplier text | SL-C9 | active | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V6 | Unreadable quote is not a terms discrepancy | SL-C9 | active | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V7 | Revised re-escalation matches the quote on file | SL-C9 | active | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V8 | No escalation before a quote is stored | SL-C9 | active | tests/integration/orchestrator/test_exam_readiness.py |
| SL-V9 | Proposal pack dumps a finished round without spending the extract key | SL-C10 | active | src/supplier_loop/cli.py, src/supplier_loop/propose.py, src/supplier_loop/operational_log/log.py, docs/proposals/PROMPT.md |
