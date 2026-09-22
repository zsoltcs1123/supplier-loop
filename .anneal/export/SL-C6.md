# SL-C6 — First live development round

**Status:** done

**Path:** SL

## Kind

new_feature

## Goal

The operator calls request_dev_round() and the loop processes that round against the real simulator. Extract may stay crude, or text-only, so this round does not spend the OpenRouter cap on vision. submit_results lands for that round.

## Deliverables

- `**MCP**` adapter behind the same simulator interface as the in-memory adapter
- .`env.example` lists `**SUPPLIER_SIM_MCP_URL**` and `**SUPPLIER_SIM_TOKEN**`
- One live request_dev_round() processed end to end
- `**WORKLOG**`.md started

## Notes

- OpenRouter vision is out of scope
- Crude extract is acceptable for this change
- The token is personal and is not stored in the repo
- Round 2 is the first request_dev_round (1/20). The loop called submit_results; echo warnings were empty. Marta has 7 line items. Declan/Tanaka/Fatima extracted empty. Tanaka and Fatima were escalated class 3/4 on empty terms.

## Sequence

6

## Dependencies

- SL-C5: Mock defect path

## Required by

- SL-C7: OpenRouter extract for PDFs and photos


## Validations



| Code | Title | Lifecycle | Change | Coverage |
| --- | --- | --- | --- | --- |
| SL-V3 | Live development round reaches submit_results | active | SL-C6 | unclaimed |

## Followups



| Code | Title | Status | Change | Converted To |
| --- | --- | --- | --- | --- |
| SL-F3 | Extract live quote bodies and attachments | done | SL-C6 | — |
| SL-F4 | Persist outbound sent log across resume | done | SL-C6 | — |
| SL-F5 | CLI flags for poll interval and max passes | done | SL-C6 | — |
