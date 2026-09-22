# SL-C2 — Mail kind classifier and fixture quote pipeline

**Status:** done

**Path:** SL

## Kind

new_feature

## Goal

Inbound fixture mail gets a kind from envelope and body shape. Only kind quote uses the extract port. The quote pipeline writes the Quote record. No live model.

## Deliverables

- Mail kind classifier: quote, question, negotiation reply, duplicate, approver ruling
- Extract port with a fixture mock. Schema is quote fields plus injection_suspected. Extra fields forbidden
- Quote record: as_sent, recomputed_total, recomputed_grand_total, optional revised_as_sent
- Normalize and validate in code. Match on description when `**SKU**` is absent
- Parser tests for mail kind against docs/fixtures/sample_traffic/emails/. Unit tests for recomputed totals. Negotiation must not change line_items here; that path waits for the defect change

## Notes

- OpenRouter and the `**PDF**` text-layer reader wait for OpenRouter extract
- The pipeline is the only writer of the Quote record
- Dedup registry stays in round state

## Sequence

2

## Dependencies

- SL-C1: In-memory simulator, round state, and operational log

## Required by

- SL-C3: Classer


## Followups



| Code | Title | Status | Change | Converted To |
| --- | --- | --- | --- | --- |
| SL-F1 | Include attachment identity in quote fingerprints | done | SL-C2 | — |
