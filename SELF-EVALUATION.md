# Self-evaluation

Honest snapshot from local logs, not from a fresh live wait. The server clock is the bottleneck: `clock_factor` on the wire often reads `1`, while a development round actually advances about 70–80 sim seconds per real second. Sitting through another full round to refresh these numbers is hours of polling.

Sources: `.artifacts/ops.jsonl`, `.artifacts/llm-spend.json`, `dev-rounds.json`, and the payload noted when development round 4 submitted. Process, tools, and hours: [WORKLOG.md](WORKLOG.md).

## What ran

Five `request_dev_round` calls. Cap 20, 15 left.

The complete unattended run is **development round 4** (2026-09-21, RFQ at 17:29 UTC, `submit_results` at 20:05 UTC). Wall time 2 h 36 min. Sim time at submit 187.9 h (~7.8 sim days). Four suppliers. Inbox traffic that round: 2 questions, 6 quotes, 1 negotiation reply, 5 approver rulings. No reminder in that window.

Payload as recorded at submit:

| Supplier | `action_taken` | `auto_approved` |
| -------- | -------------- | --------------- |
| p02      | extract        | true            |
| p03      | extract        | true            |
| p04      | escalated      | true (approved) |
| p01      | escalated      | false           |

Simulator warnings: none. p01’s class 6 mail got “need specifics” twice and no approval; the loop waited 1 sim-day and submitted `auto_approved` false.

Earlier rounds 2 and 3 also called `submit_results` for all four suppliers. Round 5 was stopped mid-inbox. A later attempt on 2026-09-22 sent RFQs, ingested one p01 quote, raised class 7, then was killed. That class 7 mail said “embedded instructions” with no quoted phrase: Extract set the flag; the text scan did not match a known needle.

## Spend

OpenRouter ledger: **$0.21 of $100**, 23 calls. Default runtime model `google/gemini-2.5-pro` is 11 of those calls and $0.19. The rest is calibration (`gpt-4o-mini`, one `gpt-4o`, one `gemini-2.5-flash`) on the Tanaka PDF and Alsayed screenshot fixtures.

## Known weaknesses

- **Clock.** Observed ~70–80×. Published `clock_factor` is not a knob and is often `1`. Live confirmation of later fixes is expensive.
- **Photo extract.** `gpt-4o-mini` misread the Alsayed screenshot (qty, size codes, grand total). `gemini-2.5-pro` read Aluminum Sheet qty 200 at 57.68, Stainless Bolt M8x40, Brass Fitting 1/2in, Epoxy Resin 5L, Plywood qty 100, grand total 16705.20, validity 14 days, terms Net 20. Photo variance is still the highest extract risk.
- **Class 7 phrasing.** Scan quotes a trapped phrase when it hits a needle (sample-014 exemption, “reviewed-and-accepted”, “no escalation required”). If only the model sets the flag, the approver mail is generic. A longer needle list does not cover a sealed exam.
- **Negotiation phrasing.** Round 4 treated “meet you at 4116.00” as a question until that shape was added as a negotiation reply.
- **Line totals.** Round 4 submitted `200 × 1.16` as `231.99999999999997`. Totals now quantize to cents before submit. Not re-checked on a full live round.
- **Description match.** Exact fold and one trailing parenthetical strip only. A fuzzy match could attach the wrong `material_id`.
- **Submit warnings.** Echo warnings are logged. The loop does not repair the payload and resubmit. Warnings are missing, unknown, or non-numeric fields; sending the same payload again does not clear them.

I would not score this as 98%. Escalation shape and the round-4 submit are the evidence. A sealed exam still has not been run.
