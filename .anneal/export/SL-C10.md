# SL-C10 — Operator proposal pack after a development round

**Status:** done

**Path:** SL

## Kind

new_feature

## Goal

After a finished development round, the operator can dump a proposal pack from round state, the operational log, submit warnings, and extract spend. A human then writes a pending proposal against a loop-contract allow-list. The quoting loop never runs that pass and never spends the extract key on it.

## Deliverables

- pack-propose `**CLI**` writes .artifacts/proposals/<round_id>`/pack.md` from files already on disk. No `**MCP**` call. No OpenRouter call.
- Operational log events include round_id so a pack can slice one round.
- docs/proposals/`**PROMPT**`.md states the allow-list, the proposal schema (pending / accepted / rejected), and that the quoting loop must not hook this pass and must not auto-apply.
- run-dev, resume-dev, and the poll pass do not call pack-propose.

## Notes

- The operator copies accepted clock numbers into the loop contract and clock constants. There is no apply command.
- The runtime extract key is not used. Cursor or the operator writes docs/proposals/<round_id>.md.
- Allow-list: reminder, quiet margin, settle wait, negotiation wait, `**SOP**` wording, Never list. Escalation classes and start_exam stay out.
- Do not run pack-propose during the exam.

## Attached documents

- design: docs/`**LOOP_CONTRACT**`.md

## Sequence

10

## Dependencies

- SL-C1: In-memory simulator, round state, and operational log


## Validations



| Code | Title | Lifecycle | Change | Coverage |
| --- | --- | --- | --- | --- |
| SL-V9 | Proposal pack dumps a finished round without spending the extract key | active | SL-C10 | src/supplier_loop/cli.py, src/supplier_loop/propose.py, src/supplier_loop/operational_log/log.py, docs/proposals/PROMPT.md |
