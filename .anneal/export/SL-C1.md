# SL-C1 — In-memory simulator, round state, and operational log

**Status:** done

**Path:** SL

## Kind

new_feature

## Goal

The loop can snapshot assignment, catalog, price history, clock, and inbox from an in-memory simulator into round state. A new round wipes round state. The operational log only appends. Business logic never calls `**MCP**`.

## Deliverables

- Simulator adapter interface. In-memory adapter covers get_assignment, get_supplier_directory, get_price_history, list_inbox, read_email, download_attachment, get_sim_clock, send_email, and submit_results
- Round state: `**RFQ**` context, per-supplier facts, Quote record slot, dedup registry, own quote history. No action_taken. No auto_approved
- Operational log, append-only, not truncated on round change
- Unit tests against the in-memory adapter. No live `**MCP**`

## Notes

- The `**MCP**` adapter waits for the first live development round
- No shared store interface. Round state and the log are separate modules
- Dedup fingerprints live in round state, not in mail kind

## Sequence

1

## Required by

- SL-C2: Mail kind classifier and fixture quote pipeline
- SL-C10: Operator proposal pack after a development round
