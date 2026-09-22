# SEED vs challenge review

- **Started:** Friday, Sep 18, 2026, 4:39 PM (UTC+2)
- **Session ID:** `994dc5d9-9b6a-4eb2-874a-5a07dd03b7ad`
- **Project:** `supplier-loop`
- **User turns:** 19
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/994dc5d9-9b6a-4eb2-874a-5a07dd03b7ad/994dc5d9-9b6a-4eb2-874a-5a07dd03b7ad.jsonl`
- **Opening prompt:** review my project @SEED.md against @challenge.md

---

## User 1

review my project @SEED.md against @challenge.md

## Assistant

I will read the challenge, the seed, and the caveman style rule first, then score the project against the brief.
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

SEED and brief are in. Next I check starter-pack rules and the repo so the review scores the seed against the real spec, not just the two files.
[tool: Glob]
[tool: Glob]
[tool: Glob]
[tool: Glob]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

**Verdict:** Seed matches challenge on architecture and safety classes. Not a complete exam spec. Gaps sit in scorecard deliverables and FAQ edge cases. This folder is plan only. No loop code yet.

Treat `challenge.md` as technical spec + scorecard. Treat `message.md` as commercial/timing override. Seed already does that. Correct.

---

**What seed gets right**

Deterministic-first. LLM only for unstructured extract. Escalate/not-escalate stays in code. That matches the brief rule: agent never verifies its own work.

Must-escalate 1–7 and must-not (arithmetic, duplicate, silence, clarifying question) match the published rulebook.

As-sent numbers, recomputed totals, action precedence, injection fail, completeness, one RFQ per supplier, one-shot `start_exam`, 8 real hours before deadline, 20 replacing dev rounds, state vs log: all present.

24h exam announce from Gergely’s note also clears the brief’s 2h floor. Keep 24h.

---

**Two-doc conflict. Seed picked the right commercial side.**

`challenge.md`: paid $500, IP assign on pay, 5 calendar days from credentials, 7 mandatory deliverables, announce exam 2h before.

`message.md`: unpaid, no IP, confirm a day, ~24h announce, shorter deliverable list.

Seed follows `message.md` for pay/IP/date. Good.

Seed then treats the shorter list as maybe-optional. That is the weak call. Honesty of self-evaluation is still a judging row. Trigger design and prior-quote accuracy are still named deliverables in the brief. Default: ship them unless Gergely waives in writing.

---

**Scorecard holes**

`SEED.md` L89–93, L201–213: trigger is a poll bullet, not deliverable 2. Brief wants a cheap deterministic pre-check (new mail? validity near expiry?) that gates the full loop. Name it as its own artifact in the contract.

Prior-quote accuracy is deliverable 4. Seed stores quote history. Seed never makes “cite earlier quotes exactly” a pass bar. A wrong number in an escalation body fails this even if the escalate/not-escalate class is right.

Self-eval + ~3 min screen recording: seed says confirm if unsure. Confirm, yes. Do not drop them while waiting. Scorecard still grades honesty.

Pipeline on L116 stops at act. Template SOP step 7: re-read own sent record. Agent never verifies from memory. Add a verify stage that checks the MCP send/inbox record, not the model.

---

**Measured-metric holes. These fail the scorer if you implement the seed as written.**

`auto_approved` on L224 is half-right. Clean quote, no escalate: set `true` (you approved it). Must-escalate case: `true` only after the approver approved. Seed states only the second half. Marking every clean quote `false` looks like you never approved.

Correction vs negotiation. Mix them and extraction breaks.

- Correction (missing line, qty, terms, validity): revised quote **replaces** the original for extract. One correction request. Second is noise.
- Negotiation (price): state a plain total in the body. One exchange. Outcome always escalates. `line_items` stay the **original** document. Negotiated figure lives in escalation + state, not in `submit_results` lines.

Seed lumps both as “revised quote.” Split them.

Approver rules on the strongest issue on file. Content discrepancy outranks negotiation. Name that issue. Seed silent.

Match quote lines on description when SKU is missing. Extra or unknown `material_id` in `submit_results` counts against extraction. Seed silent.

No “round over” signal. FAQ 5: round is done when every relevant supplier has quoted, or been reminded then quoted, or been escalated and ruled, and inbox stays quiet for a sim-time margin. Seed leaves stop conditions to a later contract. Lock a rule now.

Silent supplier still belongs in `submit_results` (completeness). Payload shape unspecified.

OpenRouter key is $100 hard cap for **dev + exam together**. Seed omits the cap. Burn it in practice, exam has no model.

---

**Process holes**

Strategy questions (“is this the right reminder threshold?”) only in the first 24h after **credentials**. Spec/schema questions any time. Blocking any time. Seed omits the window.

Brief asks for Claude Code transcripts. You build in Cursor. Seed already flags this. Ask in writing now, not at hand-in.

5-day clock in the brief starts at the credentials email. Token is not in this repo. Clock may not have started. “Early next week” is a preference, not the window.

---

**Do not change**

Deterministic validator. No LangGraph default. Spec files under `docs/spec/` as source of truth. Do not copy more rule text into the seed.

---

**What I would lock before bootstrap**

1. Email Gergely: submit day, Cursor transcripts OK, self-eval + recording still required.
2. Split correction vs negotiation in the seed.
3. Fix `auto_approved`.
4. Add verify-against-sent-record, round-done rule, one-correction cap, description matching, strongest-issue order, $100 model budget.
5. Ship trigger note + prior-quote accuracy as first-class, not implied.

Want me to patch `SEED.md` with those locks?

## User 2

1. yes I will email dont worry about that. not a seed concern. cursor is ok. recording not needed. self eval I may add.
patch the rest

## Assistant

Admin stays with you. I will lock the remaining exam rules into `SEED.md`.
[tool: Read]

## Assistant

Admin and recording stay out. I will lock trigger, prior-quote accuracy, `auto_approved`, correction vs negotiation, and the other exam rules into the seed.
[tool: Write]

## Assistant

Seed patched. Email, date, Cursor ask stay out of the file.

Locked in:

- Trigger as named SOP step 1, not implied poll
- Prior-quote accuracy as a pass bar
- Completeness includes silent suppliers; no invented lines
- Correction vs negotiation split, one request each
- Strongest-issue order
- Description match when SKU missing
- Verify against MCP sent/inbox record
- Round-done rule (quiet margin still yours to pick)
- `auto_approved`: true on clean unescalated quote; true after approver only when escalated
- OpenRouter $100 covers dev + exam
- Cursor transcripts OK
- Screen recording out
- Self-eval optional

Open left: reminder threshold, quiet margin, poll interval, model id, iteration cap.

## User 3

plan solid now? no unadressed issues left?

## Assistant

I will re-read the patched seed against the brief and FAQ, then say what is still open versus what is correctly deferred.
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

**Solid enough to bootstrap. Not zero gaps.**

Seed now covers the scorecard, the rulebook split, and the failure modes that kill measured metrics. Remaining items are either unpublished knobs (correctly left open) or a few locks I would still write.

**Correctly open (not seed bugs)**

Reminder threshold, quiet margin, poll vs clock, model id, iteration cap. Spec hides these on purpose. Calibrate in dev.

**Still unaddressed, seed-level**

1. **Missing-line scope.** Rule 1 vs FAQ 11. Supplier quotes only what they carry. Escalate missing lines in `BOM ∩ that supplier’s catalog`, not the full BOM. Escalate the full BOM and every partial catalog looks like a must-escalate. Seed never locks this. Biggest leftover.

2. **Several issues, several emails.** Seed says one issue per email, strongest first. Spec also: two concerns = two emails. “Strongest first” can be read as “send only the strongest.” Send every class as its own mail. Approver still rules on the strongest on file.

3. **New `round_id` wipes local state.** `request_dev_round()` replaces the round. Durable state keyed by old round will skip RFQs or reuse quotes. Seed tracks `round_id`. It never says reset on change.

4. **Injection: flag vs decide.** Safety stay in code. Detecting an instruction in a photo/PDF almost needs a model. Seed should say: model may set an `injection_suspected` flag on extract; code always escalates if that flag is set; model never chooses to obey.

**Spec hole you cannot lock**

Silent supplier still needs every `submit_results` field. Seed says do not invent lines. Right. Echo may still warn. Handle from live traffic, not from the seed.

**Exam ops, not seed**

Process must stay up for hours (restart-safe state is not a supervisor). Meter OpenRouter. Photo extract is still the high-variance risk.

**Bottom line:** plan is good. Lock item 1 before you write the validator. Items 2–4 are one-liners. Rest wait for code and a real `request_dev_round()`.

## User 4

lock those 4

## Assistant

I will lock the four leftover rules into the seed: missing-line scope, one email per issue, round-id state wipe, and injection flag vs decide.
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: StrReplace]
[tool: StrReplace]

## Assistant

Four locks in.

1. **Missing line** = `BOM ∩` that supplier’s catalog. Do not escalate lines they do not carry.
2. **Several classes** = several emails. Send every class. Approver still rules on the strongest. Do not drop the rest.
3. **New `round_id`** wipes mutable state. Log stays append-only and is not memory.
4. **Injection:** model may set `injection_suspected`. Code always escalates class 7 if flagged. Model never obeys.

## User 5

/technical-writing and /unslop on @SEED.md

## User 6

/unslop @SEED.md

## Assistant

I'll read `SEED.md` and rewrite it against the unslop and technical-writing rules.
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

I'll rewrite `SEED.md` as explanation: whole sentences, one name per thing, no em dashes or label-colon bullets.
[tool: Write]

## Assistant

[tool: Grep]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Grep]

## Assistant

[tool: StrReplace]

## Assistant

Seed rewritten. Meaning stayed. AI tells went.

Cut em dashes, label-colon bullets, arrows, dropped articles, `e.g.`, slashes in prose, and `file(s)`. Headings are sentence case and say the point. Spec paths and locked rules are the same.

One leftover jargon word, `hardening`, is now "reliability work the exam does not measure". No new abstract-metaphor offender for `unslop` rule 26. `combo trigger` and `noise` stay because the brief and FAQ use them.

## User 7

what is the purpose of starter_pack/example artifacts? do we need them? not mentioned as spec files to be copied. also, sample_emails is already extracted to emails I think, could be deleted

## Assistant

I'll check what those folders actually contain and whether the seed already covers the extracted sample mail.
[tool: Glob]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Glob]
[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Shell]
[tool: Read]
[tool: Read]

## Assistant

[tool: Shell]
[tool: Read]

## Assistant

[tool: Shell]

## Assistant

**`example_artifacts` is not spec.** Brief calls it “example attachments”: one sample of each quote type so you see the parse terrain before a live round.

In the pack that is:

- `inline-text_email_body.txt`
- `pasted-table_email_body.txt`
- `pdf_email_body.txt` + `pdf_tanaka-offer.pdf`
- `photo_email_body.txt` + `photo_alsayed_screen.png`

No rules, no schema, no MCP contract. Do not copy it into `docs/spec/`. Seed is right to omit it from that list.

**Need it?** No, not if you already use `sample_traffic/`. That folder has all four styles, 20 emails, attachments, timing, and `SAMPLE-TRAFFIC.html`. The examples are a smaller labeled set of the same idea. Keep them as a 10-second look at each type. Point parsers at `sample_traffic/emails/`.

**`sample_emails.zip`:** yes, duplicate. Same 31 files as `emails/` plus `attachments/` and `index.csv`. The zip uses Windows path separators. Safe to delete. Keep `emails/` and the HTML or PDF dump.

I did not delete anything. Say if you want the zip gone and the seed to list `example_artifacts` as fixtures, not spec.

## User 8

ok to both

## Assistant

I'll delete the zip and add `example_artifacts` to the seed as fixtures, not spec.
[tool: Delete]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Shell]

## Assistant

`sample_emails.zip` is gone. `emails/` stays.

Seed now splits the two:

- `docs/spec/` is the markdown rules only.
- `docs/fixtures/` is `example_artifacts/` plus `sample_traffic/`. Not spec. Parsers use `docs/fixtures/sample_traffic/emails/`. The example folder is a first look at each type.

## User 9

Build sessions use the Cursor subscription, not OpenRouter. - how do u imagine that? python code needs to call an llm endpoint. cursor is local agent.

## Assistant

You're right. The loop cannot call Cursor. I'll read that seed line and split build cost from the runtime API.
[tool: Grep]
[tool: Read]

## Assistant

[tool: StrReplace]

## Assistant

[tool: StrReplace]

## Assistant

You are right. That line mixed two wallets.

Cursor is you writing the loop in this editor. Transcripts, planning, code. The Python process never talks to Cursor.

The loop calls OpenRouter over HTTP with `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`. Extract from text, tables, PDFs, and photos, including the `injection_suspected` flag, happens there. Dev rounds and the exam share the same $100 cap.

FAQ means: do not burn the OpenRouter key while you code. Burn it only when the running loop hits an LLM.

Seed now says that. Model id is still yours to pick.

## User 10

can you consolidate @SEED.md by dropping any duplicated info, finding redundancies, dropping low-value parts. i want a high signal to noise ratio and every fact should be just stated once.

make sure nothing important is lost
estime line count savings.

## Assistant

I'll map every repeated fact in `SEED.md` and propose a single-statement cut that keeps the locks.
[tool: Read]
[tool: Read]

## Assistant

[tool: CreatePlan]

## User 11

Consolidate SEED.md

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## Assistant

I'll rewrite `SEED.md` to the 14-section outline first, then grep for leftover recap.
[tool: TodoWrite]
[tool: Read]

## Assistant

[tool: Write]

## Assistant

[tool: TodoWrite]
[tool: Grep]
[tool: Shell]

## Assistant

[tool: Grep]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Grep]
[tool: Grep]
[tool: Shell]

## Assistant

[tool: Shell]
[tool: TodoWrite]

## Assistant

Seed is 177 lines, down from 311. About 134 lines gone, 43%.

Dropped the recap blocks: already decided, failure list, escalation restatement, who it is for, what this is not, how you develop.

Each lock has one home. Score is the bar. Loop is behavior. Data is payload. Runtime is the HTTP key. Open decisions stay at the end.

Locks still in: injection flag, missing-line scope, several emails, correction vs negotiation, `auto_approved`, `round_id` wipe, combo trigger, silent supplier with no invented lines, latest `submit_results` graded.

## User 12

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## User 13

can u sketch a diagram for the loop. mark the points when llm is involved.

## Assistant

[REDACTED]

## User 14

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## User 15

can u sketch a diagram for the loop. mark the points when llm is involved.
also, organize the info in that section a better structure than just simple paragraph

## Assistant

I'll read the Loop section and the visualize skill, then add a diagram with LLM steps marked and restructure that section.
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

I'll put a mermaid pass diagram in Loop, mark Extract as the only LLM step, and split that section by stage.
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: StrReplace]

## Assistant

Loop section now follows the pass: Trigger, Ingest, Extract, Normalize, Validate, Decide and act, Verify and submit.

Diagram sits at the top. The **Extract LLM** node is the only model call. Photos go there as vision. PDF text layer is code, then Extract. Everything else is code or templates.

Dropped the duplicate one-line pipeline from Design.

## User 16

do the same with data. also, in spec and fixtures, use links

## Assistant

I'll restructure Data like Loop, and turn the spec and fixture paths into links.
[tool: Read]
[tool: Glob]

## Assistant

[tool: StrReplace]
[tool: StrReplace]

## User 17

also, mermaid chart not rendering for some reason

## Assistant

I'll check the mermaid blocks and current Mermaid syntax so the diagrams render in preview.
[tool: Read]
[tool: GetDynamicTools]

## Assistant

[tool: CallDynamicTool]
[tool: Read]
[tool: WebSearch]

## Assistant

[tool: CallDynamicTool]
[tool: WebFetch]

## Assistant

[tool: StrReplace]
[tool: StrReplace]

## Assistant

Two separate issues.

**Source tab never draws Mermaid.** You see the fence as code. That is normal. Open Markdown preview (`Markdown: Open Preview`), or view the file on GitHub. Cursor Plan/Chat render Mermaid. Regular `.md` files often do not, unless you install Markdown Preview Mermaid Support.

**Syntax was also fragile.** Unquoted `Per-RFQ` hyphens and a long `A --> B --> C` chain can fail the parser. Both charts now use `graph TD`, quoted labels, and one edge per line.

If preview still shows a code block after a reload, it is the Cursor preview gap, not the diagram.

## User 18

nah mermaid doesnt render in markdown preview. do I need an extension for that? i dont think so

## Assistant

I'll check current Cursor docs on Mermaid in markdown preview, not old VS Code advice.
[tool: Read]
[tool: WebSearch]

## Assistant

You are right for chat and Plan. Those draw Mermaid with no extension.

You are wrong for a normal `.md` file preview. Cursor staff say the built-in `Markdown: Open Preview` has no Mermaid. Chat and Plan use a different renderer. Regular preview does not.

Workarounds:

- Install **Markdown Preview Mermaid Support** (`bierner.markdown-mermaid`). That is the official answer. The Marketplace marks it deprecated because VS Code 1.121 absorbed it. Cursor preview has not.
- Open the file on GitHub. GitHub draws the fence.
- Paste the chart into chat. Chat draws it.

The seed is fine. The preview pane is the gap.

## User 19

can h make it horizontal

## Assistant

[tool: Grep]

## Assistant

[tool: StrReplace]

## Assistant

[tool: StrReplace]

## Assistant

Both charts are `graph LR` now. Loop reads left to right. Data has Simulator on the left, state in the middle, `submit_results` on the right. Tools inside those boxes still stack.
