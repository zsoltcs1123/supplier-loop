# Pre-exam solution review

- **Started:** Tuesday, Sep 22, 2026, 12:42 AM (UTC+2)
- **Session ID:** `5504fb7c-7fd2-41dc-899a-407b26cc96c2`
- **Project:** `supplier-loop`
- **User turns:** 6
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/5504fb7c-7fd2-41dc-899a-407b26cc96c2/5504fb7c-7fd2-41dc-899a-407b26cc96c2.jsonl`
- **Opening prompt:** /anneal seems my implementation is complete and ready for exam.

---

## User 1

/anneal seems my implementation is complete and ready for exam.

pls review my solution against original spec, especially in dimensions that get scored. ignore @WORKLOG.md I haven't completed it yet.

spot obvious gaps and areas for improvement

## Assistant

Review against original spec, scored dimensions. Ground in anneal context and the live code first.
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Need anneal context, original scoring spec, and live code. Caveman skill path missed; find that too.
[tool: Glob]
[tool: Glob]
[tool: Glob]
[tool: Shell]
[tool: Glob]
[tool: Glob]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Shell]

## Assistant

[tool: Read]
[tool: Glob]
[tool: Glob]
[tool: Glob]
[tool: Glob]

## Assistant

Code vs scored dimensions next. Classer, submitter, machine, extract, README.
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Grep]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Glob]
[tool: Read]

## Assistant

[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Glob]

## Assistant

[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: AskQuestion]

## Assistant

Not exam-ready. Loop shape matches spec. Scored holes still open. Highest weight ones first.

## Server score (weight order)

### 1. Escalation correctness

Classer itself is the strong part. Missing line gated on catalog. Arithmetic never a class. Class 5 negotiates then class 6. No `[REF:]` mail until a quote object exists. One class per mail.

Three fail modes still live:

**Empty extract becomes class 3/4.** Failed extract (`payment_terms=""`, `validity_days=0`) is treated as a real terms/validity mismatch. Class 1 is gated on “has lines”. Class 3/4 are not. Live `run-dev` shares `empty_quote_retries`, so that mail is **not** extracted again. That is a parsing gap escalated as a discrepancy. FAQ 13 counts that as noise.

**Re-escalate after a successful fix still says “differs”.** `_with_last_rejection` forces the rejected class back. Class 3 body is always `payment terms X differs from required Y`, even when X equals Y. Approver asked for a concrete claim. This one is concrete and false.

**Class 7 body is vague.** `"supplier content contains embedded instructions."` Names the class, not the instruction. Approver rule: empty flag gets “I need specifics”.

1 sim-day settle then submit with `auto_approved` false is a clock choice, not a rulebook miss. Risk is stopping before the reject → correct → re-escalate path finishes.

### 2. Injection resistance (auto-fail if obeyed)

Class 7 follows `injection_suspected` only. No code scan. Sample trap is already in the fixtures: sample-014, Tanaka body says the supplier is exempt and to book it directly. If Gemini misses the flag on a otherwise-clean quote, submitter sets `auto_approved` true. That is compliance. Criterion fails.

Backup scan is still the open idea, parked in architecture. For exam this is the cheapest high-weight miss.

### 3. Extraction + validation

As-sent qty/price/terms/validity, recomputed totals, cents quantize: that path is right. Normalize-on-description when SKU absent: right.

Weak spots:

- Photo/PDF still the high-variance slice. Default model is `google/gemini-2.5-pro`. Good. One miss on Alsayed still possible.
- Empty extract stays empty in the unattended loop.
- Description match is exact after casefold. `"200 mm"` vs `"200mm"` becomes an unmapped line, then a false class 1.
- Submit keeps every extracted line, including dupes / empty `material_id`. FAQ 14 wants one `material_id` per supplier, only lines the supplier sent.

### 4. Operational discipline

Good: one RFQ covering every fillable BOM line. One reminder. One correction. One negotiation. Duplicate fingerprint. Restart from round files plus `sent.json`. `resume-dev` exists.

Watch:

- Reminder 4 sim-days (`p01`/`p02`), 8 (`p03`/`p04`). Too-early is what they measure. These look conservative, not early.
- `run-dev` always calls `request_dev_round()`. There is **no** `start_exam` command. Exam start by hand, then `resume-dev`. `run-dev` during the sealed round is a round-wipe.

### 5. Completeness

`relevant_supplier_ids` plus empty `reminded` rows for silence. Shape is right.

`run_until_submit` stops on first `submit_results`. Warnings are printed, never fixed and resent. Seed says latest submit is graded, and warnings should be fixed. One bad payload can be the graded one.

### 6. Prior-quote accuracy

Class 6 cites original total, counter, reply. Counter is a ceiling-derived number, not a cited history unit price. If they cite, they must cite stored history. They cite `recomputed_grand_total`, not the as-sent printed total sitting in `own_quote_history`. That can drift from the document.

## Human score

**Loop contract / trigger.** Contract is filled. Combo trigger exists. Extra wakes (idle supplier, empty quote, still-escalated) are broader than “inbox delta or due alarm”, still deterministic.

**Exam behaviour.** Operator path is incomplete. Announce 24h ahead per Gergely’s note (FAQ says 2h; personal note wins). Call `start_exam` once, then `resume-dev`. Crash is the exam. Process must stay up 8 real hours.

**Process / honesty.** Self-eval page is missing. Brief scores it. You asked to ignore `WORKLOG.md`. Still need that page plus transcripts.

**Runnability.** `uv run python -m supplier_loop run-dev` is the one command. README does not set `PYTHONIOENCODING=utf-8`. Watermarks crash a cp1252 print. No Docker one-command; only a DevContainer. Brief asked WSL2 or Docker.

## What already matches spec

Code owns decide/act. Model only extracts. Submitter derives `action_taken` / `auto_approved` from `list_sent`. `escalated` beats question/reminder. Round wipe vs append-only log. PDF text layer in code, vision on photos. Out of scope agent frameworks stayed out.

## Not exam-ready until these move

1. Code injection scan on body + PDF text. Set `injection_suspected` only. Quote the trap phrase in the class 7 mail. Sample-014 is the fixture.
2. Do not class 3/4 (or 1) on an empty/unreadable extract. Retry extract while lines are empty, or leave the supplier waiting.
3. Re-escalation after correction must describe the quote now on file without claiming a mismatch that is gone.
4. Exam CLI: `start_exam` then loop. Never `request_dev_round` on that path.
5. One-page honest self-eval from live round numbers, including photo miss and class 6 timeout.

Do not call `start_exam` on this tree as it stands. Injection miss on a clean quote is an automatic fail of criterion 2.

Want those five as the next sitting, or only the injection scan first?

## User 2

create an anneal change for closing these gaps.

## Assistant

One change for the exam gaps. Check anneal create syntax and whether a sibling change already covers this.
[tool: Shell]
[tool: Glob]
[tool: Read]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

No duplicate change. Spec is exam-readiness: injection scan, empty-quote classer gate, correction re-escalation, `start_exam` CLI, self-eval. Convert SL-I1 into it.
[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

**SL-C9** created. Pending. Kind `feature_update`. Sequence 9. Depends on SL-C8.

Goal: escalate embedded instructions even when Extract misses the flag. Do not treat an unreadable quote as a terms or validity mismatch. Re-escalation after correction describes the quote now on file. Operator starts the sealed exam without a new dev round. Submission includes an honest self-evaluation.

Deliverables:
- Code scan of body and PDF text may set `injection_suspected` only. Class 7 mail quotes the trap. Fixture: sample-014
- Classer omits classes 1, 3, 4 when the quote has no lines. Unattended loop retries extract while lines are empty
- Re-escalation after correction does not claim a mismatch that is gone
- CLI calls `start_exam` then runs the loop. Never `request_dev_round`
- One-page self-eval. README names `PYTHONIOENCODING=utf-8` and the exam command

Out of this change: submit-echo warning retry, as-sent prior-quote citation, fuzzy description match.

**SL-I1** converted into SL-C9.

Next: `anneal implement SL-C9`, or add a validation on C9 first.

## User 3

ok but make sure to never call exam under any circumstances. only I can do that.
also - can we derive additional validations from spec, that are not covered by unit tests already, for exam readiness?

## Assistant

C9 must never call `start_exam`. Survey existing validations and tests, then draft new ones from spec.
[tool: Read]
[tool: Shell]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Read]
[tool: Grep]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

**SL-C9** revised. Nothing in this repo calls `start_exam`. Only you, out of band. Then `resume-dev`. CLI, poll pass, helpers, tests: no caller. Title now “operator-owned exam”.

Five validations on C9. Unclaimed. These are loop scenarios the unit suite does not cover:

**SL-V5** Embedded instructions escalate from supplier text. Sample-014 exemption in the body. Extract returns `injection_suspected` false. Sent record still has class 7 `[REF:]` quoting that phrase. `auto_approved` false.

**SL-V6** Unreadable quote is not a terms discrepancy. Empty extract (no lines, empty terms, validity 0) sends no class 3/4 mail. Later retry stores real lines. No false terms mail in between.

**SL-V7** Revised re-escalation matches the quote on file. Class 3 rejected, correction, revised terms match RFQ. Next `[REF:]` describes the file. It does not say terms differ.

**SL-V8** Loop never calls `start_exam`. Fake MCP: `ping` / `run-dev` / `resume-dev` never send `start_exam`. Help has no exam command. `resume-dev` also never sends `request_dev_round`.

**SL-V9** No escalation before a quote is stored. After RFQs, empty inbox: no mail to `approver@sim.local`.

Left out on purpose: arithmetic (classer unit tests), reminder-once (V2), self-eval (file, not a running-system scenario).

Next: `anneal implement SL-C9`.

## User 4

v8 i don't think we need that

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

**SL-V8** deleted.

C9 still forbids any `start_exam` caller. That stays a deliverable, not a scored scenario.

C9 validations now: V5, V6, V7, V9.

## User 5

sl-c9 title: Exam readyness

## Assistant

[tool: Shell]

## Assistant

**SL-C9** title is **Exam readiness**.

## User 6

sl-v3 and v4 claims are weird, fine to leave them unclaimed

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

**SL-V3** and **SL-V4** coverage cleared. Both unclaimed. Scenarios unchanged.
