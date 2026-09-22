# SL-C7 — OpenRouter extract for PDFs and photos

**Status:** done

**Path:** SL

## Kind

new_feature

## Goal

Runtime extract uses the issued OpenRouter key. A `**PDF**` with a text layer is read in code first. Photos use vision. .`env.example` names `**OPENROUTER_API_KEY**` and `**OPENROUTER_MODEL**`.

## Deliverables

- OpenRouter `**HTTP**` backend on the extract port
- `**PDF**` text-layer reader is a function inside the quote pipeline, not a port
- Vision on photos and screenshots only
- .`env.example` lists `**OPENROUTER_API_KEY**` and `**OPENROUTER_MODEL**`
- Spend tracking against the $100 cap

## Notes

- Unit and orchestrator work keep the fixture mock and the in-memory simulator
- Extra fields stay forbidden on the extract port
- Exam model default is openai/gpt-4o-mini
- Round 3 (2/20): Tanaka and Fatima never quoted; submitted empty after quiet. Tanaka `**PDF**` fixture extracts. Alsayed screenshot does not on gpt-4o-mini.

## Sequence

7

## Dependencies

- SL-C6: First live development round

## Required by

- SL-C8: Unattended live round


## Followups



| Code | Title | Status | Change | Converted To |
| --- | --- | --- | --- | --- |
| SL-F6 | Retune photo extract against the Alsayed screenshot fixture | done | SL-C7 | — |
| SL-F7 | Hold silent PDF and photo suppliers past one quiet day | done | SL-C7 | — |
