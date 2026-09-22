# Changes

## SL — Supplier Loop

| Code | Title | Goal | Status |
| --- | --- | --- | --- |
| SL-C1 | In-memory simulator, round state, and operational log | The loop can snapshot assignment, catalog, price history, clock, and inbox from an in-memory simulator into round state. A new round wipes round state. The operational log only appends. Business logic never calls MCP. | done |
| SL-C2 | Mail kind classifier and fixture quote pipeline | Inbound fixture mail gets a kind from envelope and body shape. Only kind quote uses the extract port. The quote pipeline writes the Quote record. No live model. | done |
| SL-C3 | Classer | Given a Quote record, RFQ context, price history, injection_suspected, and own quote history, code returns the set of required escalation classes. The classer does not write auto_approved or action_taken. | done |
| SL-C4 | Mock happy-path round | On the in-memory simulator, the loop runs a pass when inbox delta is non-empty, sends one RFQ per relevant supplier, extracts a clean quote, and calls submit_results. The submitter derives action_taken and auto_approved from stored facts plus the sent record. | done |
| SL-C5 | Mock defect path | On the in-memory simulator, the loop reminds once on reminder_due, answers a question without extract, requests one correction, negotiates once, and sends every required class. The submitter derives the strongest action_taken from facts plus the sent record. | done |
| SL-C6 | First live development round | The operator calls request_dev_round() and the loop processes that round against the real simulator. Extract may stay crude, or text-only, so this round does not spend the OpenRouter cap on vision. submit_results lands for that round. | done |
| SL-C7 | OpenRouter extract for PDFs and photos | Runtime extract uses the issued OpenRouter key. A PDF with a text layer is read in code first. Photos use vision. .env.example names OPENROUTER_API_KEY and OPENROUTER_MODEL. | done |
| SL-C8 | Unattended live round | The loop completes a live development round without you driving individual acts. Reminder threshold, inbox-quiet margin, poll interval, and iteration cap are set from that run. The loop contract is filled. README is one command. | done |
| SL-C9 | Exam readiness | The loop escalates embedded supplier instructions even when Extract misses the flag, and it does not treat an unreadable quote as a terms or validity discrepancy. After a correction, the re-escalation describes the quote now on file. The loop never calls start_exam. Only the operator does, out of band; resume-dev then runs against that round. The submission includes an honest self-evaluation. | done |
| SL-C10 | Operator proposal pack after a development round | After a finished development round, the operator can dump a proposal pack from round state, the operational log, submit warnings, and extract spend. A human then writes a pending proposal against a loop-contract allow-list. The quoting loop never runs that pass and never spends the extract key on it. | done |
