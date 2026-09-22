# Code review: SL-C2 to SL-C5

- **Started:** Monday, Sep 21, 2026, 1:56 PM (UTC+2)
- **Session ID:** `41ac53df-3010-4296-8bc9-53934fa11b7e`
- **Project:** `supplier-loop`
- **User turns:** 3
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/41ac53df-3010-4296-8bc9-53934fa11b7e/41ac53df-3010-4296-8bc9-53934fa11b7e.jsonl`
- **Opening prompt:** /code-review current branch vs main

---

## User 1

/code-review current branch vs main
check against /anneal changes: sl-c2 to sl-c5

## Assistant

I'll review the current branch against main, and check it against anneal changes sl-c2 through sl-c5. First I load the review layers, anneal entity rules, and the branch diff.
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Next I pull the branch diff, anneal change specs for sl-c2–sl-c5, and the project coding rules so the review has a real baseline.
[tool: Glob]
[tool: Glob]
[tool: Shell]
[tool: Shell]
[tool: Glob]
[tool: Glob]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Shell]
[tool: Read]
[tool: Read]

## Assistant

Now I read production modules, specs, and tests for C2–C5 so findings sit on the actual code.
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
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

[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Glob]

## Assistant

[tool: Read]
[tool: Read]
[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Grep]
[tool: Grep]
[tool: Grep]

## Assistant

[tool: Grep]
[tool: Read]
[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Branch `feat/c2-c5` vs `main`: mail kind, fixture extract, classer, mock happy path, mock defect path. Matches C2–C5 shape. Spec holes sit in negotiation escalate and a few seams.

## Summary

Loop now classifies inbound mail, writes a Quote record from a fixture extractor, returns escalation classes in code, then runs an in-memory pass: RFQ, extract, remind, question, correct, negotiate, submit from sent-record evidence.

## Findings by layer

**1 Code quality**
- **Major** — Class 6 escalate runs in same pass as counter-offer; body has no numbers (`machine/advance.py:25`, `machine/escalate.py:93`)
- **Medium** — Number-only negotiation reply falls through to `question`, so `answer_question` fires (`mail_kind/classify.py:38`, `mail_kind/classify.py:56`)
- **Medium** — Quote fingerprint is sender+subject; same-subject revised quote becomes `duplicate` (`round_state/fingerprint.py:4`)
- **Medium** — `_needs_reminder` and missing-line/qty helpers duplicated (`machine/due.py:27`, `machine/remind.py:49`, `machine/escalate.py:100`, `machine/correct.py:59`)
- **Minor** — Nested list-comp used as a let-binding (`machine/correct.py:37`)

**2 Conventions**
- **Medium** — Machine imports `orchestrator.relevance`; dependency points the wrong way (`machine/advance.py:4`, `machine/escalate.py:1`, `machine/happy.py:5`)
- **Medium** — Orchestrator branches on `InMemorySimulator` (`orchestrator/run.py:144`)
- **Medium** — Phase `rfq_sent` never assigned; happy path jumps `idle` → `awaiting_quote` (`machine/happy.py:39`)
- **Medium** — Inline import in integration test (`tests/integration/orchestrator/test_defect_path.py:363`)

**3 Principles**
- **Medium** — Same duplication as layer 1 (Simplicity / SLAP)

**4 Security**
- No issues. Extra extract fields forbidden. Class 7 follows `injection_suspected` only.

**5 Testing**
- **Medium** — No test that several classes send several `[REF:]` mails in one pass (C5 deliverable)
- **Medium** — Submitter never asserts `answered_question` (C5 action precedence)
- **Minor** — Mail-kind subset tests repeat the full sample-traffic parametrize (`tests/unit/mail_kind/test_classify.py:57-104`)
- **Minor** — Defect-path happy regression plus ingest raw-body test repeat existing coverage

**6 Spec (C2–C5 + exam rules)**
- **Major** — FAQ 15: wait for negotiation reply, then escalate class 6 with both numbers. Code does neither.
- **Medium** — C5: number-only negotiation replies. Classifier only matches `"meet in the middle"`.
- **Medium** — After approver approval, `auto_approved` stays false; `approver_rulings` stored, never read (`submitter/submit.py:26`, `machine/ruling.py:22`). RFQ_FORMAT conflicts with FAQ/SEED here.
- **Medium** — Forced re-escalate via `last_rejection_class` can send an empty claim. Already tracked as followup on C5 (`machine/advance.py:17`).
- C2–C4 core deliverables hold: five mail kinds, fixture extract, Quote record, normalize-on-description, classer 1–7, happy-path `extract` + `auto_approved true`, one RFQ per relevant supplier, inject → class 7 mail + `auto_approved false`.

**Totals:** 2 Major, 12 Medium, 3 Minor.

Interactive mode. Highest severity first. Wait after each.

---

**Issue 1 (Major)** — Class 6 escalate is premature and empty.

FAQ 15: supplier answers one exchange, then escalate **with both numbers**. Code sends the counter, writes `own_quote_history` immediately, classer sees history, class 6 mail goes out in that same pass. Body is only a label.

```25:30:src/supplier_loop/machine/advance.py
            if 5 in classes and not supplier.own_quote_history:
                negotiate_once(supplier, state, simulator)
                _apply_classer(supplier, state)
                classes = list(supplier.escalation_classes)
                sent = simulator.list_sent()
            send_pending_escalations(supplier, state, simulator, sent)
```

```93:94:src/supplier_loop/machine/escalate.py
    if class_num == 6:
        return f"{marker} negotiation outcome requires approver sign-off."
```

**Fix:** After `negotiate_once`, wait for `negotiation_reply`. Then escalate class 6 with original total and counter/reply numbers. Move the class-6 send out of this pass. Update `test_orchestrator_negotiates_price_then_escalates_class_six`.

**Fix / Skip / Discuss?**

## User 2

stop walkthrough, fix all issues as per recommended, commit push and update pr

## Assistant

Stop walkthrough. Fix every listed issue, then commit, push, and update the PR. First I load git state, the PR, and the files those fixes touch.
[tool: Read]
[tool: Read]
[tool: Shell]
[tool: Grep]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Glob]
[tool: Read]

## Assistant

[tool: Grep]
[tool: Read]
[tool: Read]
[tool: TodoWrite]

## Assistant

Moving shared helpers first, then applying the behavior fixes.
[tool: Read]

## Assistant

[tool: Write]
[tool: Write]
[tool: Delete]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Write]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: Write]
[tool: StrReplace]
[tool: Write]
[tool: Write]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: Write]
[tool: Write]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]

## Assistant

Updating tests next: drop the redundant ones, then cover the new behavior.
[tool: Write]
[tool: Write]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
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

[tool: Grep]
[tool: Grep]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: Read]
[tool: Read]

## Assistant

[tool: StrReplace]
[tool: TodoWrite]
[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Read]
[tool: Shell]

## Assistant

[tool: StrReplace]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]
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

[tool: GetDynamicTools]

## Assistant

[tool: CallDynamicTool]

## Assistant

[tool: TodoWrite]

## Assistant

All review issues fixed. Pushed. PR updated.

**PR:** https://github.com/zsoltcs1123/supplier-loop/pull/6
**Commit:** `fix(supplier_loop): wait for negotiation reply before class 6`

What changed:

- Class 6 waits for the supplier reply, then cites original / counter / reply totals
- Number-only bodies classify as `negotiation_reply`, not a question
- Quote fingerprint uses sender, subject, body, attachments. Same-subject revised quote is not a duplicate
- `auto_approved` is true after an approver approval, false until then
- Re-escalation after correction describes the quote now on file
- RFQ send lands `rfq_sent`, later pass moves to `awaiting_quote`
- Relevance lives outside orchestrator. Reminder and BOM-gap helpers are shared
- Orchestrator no longer inspects `InMemorySimulator`
- Tests cover multi-class `[REF:]` mails and `answered_question`. Redundant mail-kind tests gone

Gate: 108 tests + `prek --all-files` passed.

## User 3

whats the deal with these unticked boxes on the PR:

 Happy path: two relevant suppliers get one RFQ each; irrelevant supplier gets none; first pass lands rfq_sent; second round wipes quotes and keeps the operational log
 Defect path: one reminder and no second; question skips extract; missing-line reject then correct_once then re-escalate with the quote now on file then approval sets auto_approved=true
 Over-ceiling: counter-offer first, no class 6 until a number-only reply, then class 6 with both numbers
 Several classes send several [REF:] mails; injection class 7 with auto_approved=false until approval

## Assistant

Those four boxes were a leftover reviewer checklist. Pytest already covers them. I'll tick them on the PR.
[tool: CallDynamicTool]

## Assistant

They were not leftover work. I copied the original PR scenario list as a human checklist and only ticked the two commands I ran. That was a bad split: those four cases already live in the integration tests, and that suite went green.

Ticked them on https://github.com/zsoltcs1123/supplier-loop/pull/6.
