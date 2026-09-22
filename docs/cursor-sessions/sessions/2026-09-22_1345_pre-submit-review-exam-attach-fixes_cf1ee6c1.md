# Pre-submit review + exam attach fixes

- **Started:** Tuesday, September 22, 2026 13:45 (file mtime)
- **Session ID:** `cf1ee6c1-7562-48b9-866e-30ffbe806ee8`
- **Project:** `supplier-loop`
- **User turns:** 6
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/cf1ee6c1-7562-48b9-866e-30ffbe806ee8/cf1ee6c1-7562-48b9-866e-30ffbe806ee8.jsonl`
- **Opening prompt:** check if my solution is ready to submit to gergely.

---

## User 1

check if my solution is ready to submit to gergely.

## Assistant

I'll check the project against the submission bar for Gergely. First I'm reading the contract docs and locating what "ready" means.
[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Glob]
[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Glob]

## Assistant

[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Previous review checked loop shape, not the package Gergely actually receives. I’ll audit deliverables and the gaps that would show up on a sealed exam.
[tool: Grep]
[tool: Read]
[tool: Glob]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Read]
[tool: Grep]
[tool: Glob]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Grep]
[tool: Glob]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Glob]
[tool: Grep]
[tool: Read]
[tool: Shell]

## Assistant

[tool: Read]
[tool: Read]
[tool: Shell]

## Assistant

[tool: Grep]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Grep]

## Assistant

[tool: Read]
[tool: Read]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

**Not ready to send to Gergely, and not ready to call `start_exam`.** The quoting loop is in good shape. The way you would start the sealed exam is not.

## What is solid

203 tests pass. `main` is clean and matches `origin/main`. Development round 4 finished unattended on 2026-09-21 (submit at 20:05 UTC, four suppliers, no reminder in that window). Spend is about $0.21 of $100, with 15 `request_dev_round` calls left. His email’s paper deliverables are in the repo: `docs/LOOP_CONTRACT.md`, README, `WORKLOG.md`, `SELF-EVALUATION.md`, Cursor transcripts, anneal export. The loop itself never calls `start_exam`.

## The blocker

`resume-dev` continues whatever is already on disk. It refreshes the clock and the inbox. It does not wipe state when `round_id` changes, and it does not snapshot the assignment, catalog, or price history.

Disk right now is a killed development round: mode `dev`, `RFQ-002`, p01 already `escalated` on class 7, p02–p04 still `awaiting_quote`. `start_exam` then `resume-dev` would run the sealed scenario through that old state, so the new RFQ can be skipped. `run-dev` is the other trap: it calls `request_dev_round` and replaces the exam.

README tells a reviewer to start the exam out of band and then run `resume-dev`. That command only continues the same round after a process restart. There is no command that wipes local state, snapshots the world `start_exam` just created, and polls without calling `request_dev_round`.

Do not email the 24-hour announcement until that path exists and you have seen it send RFQs on a fresh round.

## Risks to accept before the announcement

These are real, and the self-evaluation already owns most of them. They are smaller than the entry-path bug.

- This morning’s killed round set class 7 from the model alone. `injection_phrase` is empty, so the approver mail says “embedded instructions” with no quoted phrase. The scan only knows a fixed needle list. A sealed exam will use new wording. You still escalate, so you do not obey the text. A vague claim is what gets “need specifics,” and the resend repeats the same sentence.
- If `submit_results` returns warnings, the loop logs them and stops. The spec says fix and submit again. Round 4’s log line has no warning field.
- Class 6 cites the recomputed grand total, the counter, and the reply. It does not cite the as-sent document total from your own quote history. Prior-quote accuracy is scored.
- Description match is exact after folding and stripping one trailing parenthetical. An unmapped line is submitted with an empty `material_id`.
- A PDF with no text layer is not sent to the vision model.
- Cent quantization, the negotiation-reply shape, and the injection scan have not finished a full live round. The last complete unattended run is still round 4, on older code.

## After the exam path works

His note asks for the contract, the code, the `submit_results` outcome, the transcripts, `WORKLOG.md`, and a short README. Those files are ready. The round-4 payload itself lives in gitignored `.artifacts/`; the self-evaluation table is what a clone of the repo shows. The shared brief also asks for a short screen recording. His email does not. Announce about 24 hours ahead (his note; the FAQ floor is 2 hours), keep the machine awake for the whole run, and treat a crash as the exam.

## User 2

let's address the block and the easily fixable risks.

## Assistant

The exam entry path is the blocker. I’ll check which of the other risks are small code changes, and leave the hard ones out of the plan.
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Grep]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Grep]
[tool: Read]
[tool: GetDynamicTools]

## Assistant

[tool: GetDynamicTools]

## Assistant

[tool: CallDynamicTool]

## Assistant

[tool: CallDynamicTool]

## Assistant

PyMuPDF can render a pageless text layer to PNG with the API already in this repo. The other residual risks stay out: they are heuristics or a live round, not small fixes.
[tool: CreatePlan]

## User 3

the left out ones, we should make a note of in worklog or self-assessment (minus the 'another live dev round')

## Assistant

Those three leftovers belong on the honesty page Gergely reads. I’ll add that note to the plan and leave the live-round item out.
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Read]
[tool: Read]

## Assistant

The three leftovers go in `SELF-EVALUATION.md`, in place of the sentence that says class 6 citation was never claimed. That page is what Gergely scores for honesty. `WORKLOG.md` stays as the process log.

The note will cover class 7 wording when the scan misses, exact description match, and submit warnings that are logged but not repaired. Another live development round is not mentioned in either file.

## User 4

Exam attach and two small fixes

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## Assistant

I'll implement the plan in order: exam attach first, then class 6 citation and the self-evaluation note, then textless PDF vision.

[REDACTED]
[tool: TodoWrite]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Grep]
[tool: Read]
[tool: Read]

## Assistant

[REDACTED]
[tool: Read]

## Assistant

Implementing the changes now.

[REDACTED]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Read]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Read]

## Assistant

[REDACTED]
[tool: StrReplace]

## Assistant

Writing tests and running the suite.

[REDACTED]
[tool: Write]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Read]
[tool: Grep]

## Assistant

[REDACTED]
[tool: Glob]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

The CLI test was too brittle. I'll simplify it.

[REDACTED]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: StrReplace]

## Assistant

[REDACTED]
[tool: Shell]
[tool: TodoWrite]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

Plan is done. 212 tests pass.

### 1. Exam attach (`resume-dev`)
[`continue_dev_round`](src/supplier_loop/cli.py) reads the server clock first. If `round.json` is missing or `round_id` differs, it wipes local state, snapshots the new assignment, and prints `attach`. Same id keeps phase and `sent.json` for crash recovery.

[`stored_round_id`](src/supplier_loop/round_state/store.py) is the helper. [README](README.md) and [LOOP_CONTRACT](docs/LOOP_CONTRACT.md) document the behavior.

### 2. Class 6 cites as-sent total
[`_class_6_claim`](src/supplier_loop/machine/escalate.py) uses `own_quote_history[0].grand_total` when present, otherwise `quote.as_sent.grand_total`. It no longer cites the recomputed sum.

### 3. Textless PDF → vision
[`render_pdf_pages`](src/supplier_loop/quote_pipeline/pdf_text.py) renders at 150 dpi. [`_choose_extract_input`](src/supplier_loop/quote_pipeline/pipeline.py) sends PNGs to the existing vision path when PyMuPDF finds no text layer.

### 4. Self-evaluation honesty
[SELF-EVALUATION.md](SELF-EVALUATION.md) now records the three known gaps: class 7 generic mail when scan misses, exact-only description match, and submit warnings logged but not repaired.

### Exam path
1. Call `start_exam` out of band (MCP tool, not in this repo).
2. Run `uv run python -m supplier_loop resume-dev`.
3. Do not run `run-dev` after the exam starts.

The killed dev state on disk is stale. The next `resume-dev` against a different server `round_id` will wipe and attach cleanly.

[REDACTED]

## User 5

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## User 6

add the transcript of this convo to the cursor session, commit and push

## Assistant

I'll find how cursor sessions are exported in this repo, then add this conversation, commit, and push.

[REDACTED]
[tool: Read]
[tool: Glob]
[tool: Grep]
