# Anneal export — Supplier Loop

Generated 2026-09-22 10:38 UTC from the Anneal workspace in this repo.

Read-only snapshot for review. Start with [overview.md](overview.md), then drill into changes (SL-C1 through SL-C10) and validations (SL-V1 through SL-V9).

## Start here

- [Project overview](overview.md)
- [Project detail — SL](SL.md)

## List views

- [Projects](projects.md) (1)
- [Changes](changes.md) (10)
- [Knowledge](knowledge.md) (3)
- [Validations](validations.md) (9)
- [Bugs](bugs.md) (3)
- [Ideas](ideas.md) (1)
- [Followups](followups.md) (8)
- [Milestones](milestones.md) (0)

## Entities by type

### Projects

- [SL — Supplier Loop](SL.md) — live

### Changes

- [SL-C1 — In-memory simulator, round state, and operational log](SL-C1.md) — done (The loop can snapshot assignment, catalog, price history, clock, and inbox from an in-memory simulator into round state. A new round wipes round state. The operational log only appends. Business logic never calls MCP.)
- [SL-C10 — Operator proposal pack after a development round](SL-C10.md) — done (After a finished development round, the operator can dump a proposal pack from round state, the operational log, submit warnings, and extract spend. A human then writes a pending proposal against a loop-contract allow-list. The quoting loop never runs that pass and never spends the extract key on it.)
- [SL-C2 — Mail kind classifier and fixture quote pipeline](SL-C2.md) — done (Inbound fixture mail gets a kind from envelope and body shape. Only kind quote uses the extract port. The quote pipeline writes the Quote record. No live model.)
- [SL-C3 — Classer](SL-C3.md) — done (Given a Quote record, RFQ context, price history, injection_suspected, and own quote history, code returns the set of required escalation classes. The classer does not write auto_approved or action_taken.)
- [SL-C4 — Mock happy-path round](SL-C4.md) — done (On the in-memory simulator, the loop runs a pass when inbox delta is non-empty, sends one RFQ per relevant supplier, extracts a clean quote, and calls submit_results. The submitter derives action_taken and auto_approved from stored facts plus the sent record.)
- [SL-C5 — Mock defect path](SL-C5.md) — done (On the in-memory simulator, the loop reminds once on reminder_due, answers a question without extract, requests one correction, negotiates once, and sends every required class. The submitter derives the strongest action_taken from facts plus the sent record.)
- [SL-C6 — First live development round](SL-C6.md) — done (The operator calls request_dev_round() and the loop processes that round against the real simulator. Extract may stay crude, or text-only, so this round does not spend the OpenRouter cap on vision. submit_results lands for that round.)
- [SL-C7 — OpenRouter extract for PDFs and photos](SL-C7.md) — done (Runtime extract uses the issued OpenRouter key. A PDF with a text layer is read in code first. Photos use vision. .env.example names OPENROUTER_API_KEY and OPENROUTER_MODEL.)
- [SL-C8 — Unattended live round](SL-C8.md) — done (The loop completes a live development round without you driving individual acts. Reminder threshold, inbox-quiet margin, poll interval, and iteration cap are set from that run. The loop contract is filled. README is one command.)
- [SL-C9 — Exam readiness](SL-C9.md) — done (The loop escalates embedded supplier instructions even when Extract misses the flag, and it does not treat an unreadable quote as a terms or validity discrepancy. After a correction, the re-escalation describes the quote now on file. The loop never calls start_exam. Only the operator does, out of band; resume-dev then runs against that round. The submission includes an honest self-evaluation.)

### Knowledge

- [SL-K1 — Live list_inbox is inbound-only and timestamps are sim_time seconds](SL-K1.md) — active
- [SL-K2 — openai/gpt-4o-mini misreads the Alsayed screenshot fixture](SL-K2.md) — active
- [SL-K3 — Proposal pack is operator-only and never spends the extract key](SL-K3.md) — active

### Validations

- [SL-V1 — Clean quotes submit as extract](SL-V1.md) — active (SL-C4)
- [SL-V2 — Defects act once and submit from evidence](SL-V2.md) — active (SL-C5)
- [SL-V3 — Live development round reaches submit_results](SL-V3.md) — active (SL-C6)
- [SL-V4 — Unattended live round completes](SL-V4.md) — active (SL-C8)
- [SL-V5 — Embedded instructions escalate from supplier text](SL-V5.md) — active (SL-C9)
- [SL-V6 — Unreadable quote is not a terms discrepancy](SL-V6.md) — active (SL-C9)
- [SL-V7 — Revised re-escalation matches the quote on file](SL-V7.md) — active (SL-C9)
- [SL-V8 — No escalation before a quote is stored](SL-V8.md) — active (SL-C9)
- [SL-V9 — Proposal pack dumps a finished round without spending the extract key](SL-V9.md) — active (SL-C10)

### Bugs

- [SL-B1 — Empty extract still escalates class 1](SL-B1.md) — done (medium)
- [SL-B2 — Approver Not approving counts as approval](SL-B2.md) — done (high)
- [SL-B3 — Recomputed line total can be a binary float](SL-B3.md) — done (low)

### Ideas

- [SL-I1 — Scan raw supplier text for instruction-like phrases and hidden unicode](SL-I1.md) — converted

### Followups

- [SL-F1 — Include attachment identity in quote fingerprints](SL-F1.md) — done (SL-C2)
- [SL-F2 — Re-escalation after correction must describe the quote now on file](SL-F2.md) — done (SL-C5)
- [SL-F3 — Extract live quote bodies and attachments](SL-F3.md) — done (SL-C6)
- [SL-F4 — Persist outbound sent log across resume](SL-F4.md) — done (SL-C6)
- [SL-F5 — CLI flags for poll interval and max passes](SL-F5.md) — done (SL-C6)
- [SL-F6 — Retune photo extract against the Alsayed screenshot fixture](SL-F6.md) — done (SL-C7)
- [SL-F7 — Hold silent PDF and photo suppliers past one quiet day](SL-F7.md) — done (SL-C7)
- [SL-F8 — Resend the concrete claim when the approver asks for specifics](SL-F8.md) — done (SL-C8)

## Counts

- Entity files: 35
- List views: 8
- Overview: 1
- Index: 1
- Total markdown files: 45
