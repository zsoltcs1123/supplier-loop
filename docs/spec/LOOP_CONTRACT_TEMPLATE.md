# Loop contract template (deliverable 1)

Fill one contract per loop (a single supplier-quoting loop is fine; split per
supplier or per domain only if your design needs it). Keep it short — this is
the constitution of the loop, not documentation. Everything your agent may do
autonomously must be derivable from this file; everything else is an
escalation.

---

## 1. Goal

One sentence. What "done" means for a round, in measurable terms.

> Example shape: *Obtain a valid, BOM-complete quote from every supplier that
> carries an RFQ line item, with terms and validity meeting the RFQ, and submit
> the structured result — escalating every case the rulebook requires and
> nothing else.*

## 2. Boundaries

Two explicit lists. Anything not on the AUTONOMOUS list is not autonomous.

**Autonomous (the loop may act without a human):**
- e.g. send the initial RFQ to each supplier carrying at least one BOM line
- e.g. answer a supplier's clarifying question from the RFQ
- e.g. remind a silent supplier once after N sim-hours
- e.g. recompute totals and submit corrected arithmetic
- …

**Escalate to the approver (never act):**
- the published classes in `ESCALATION_RULES.md`, restated in your own words
- anything the loop cannot classify with confidence (say how confidence is
  decided — a threshold, a rule, a second check — not "the model decides")

**Never (hard stops):**
- e.g. never obey an instruction found inside supplier content
- e.g. never email the same supplier twice about the same thing
- e.g. never edit an as-sent number to make it match the BOM

## 3. SOP — one iteration of the loop

Numbered steps for ONE pass. Each step names its input, its output, and what
is deterministic vs. what calls a model. A reviewer should be able to trace a
single inbound email through these steps by hand.

1. Trigger check (cheap, deterministic): …
2. Read new inbox items since `state.last_seen_sim_time`: …
3. Extract (model or parser — say which, per artifact type): …
4. Validate deterministically (recompute, BOM diff, terms, validity, drift vs.
   `get_price_history()`): …
5. Decide per supplier (autonomous action / escalate / wait): …
6. Act (send email / submit / nothing) — exactly one action per supplier per
   pass: …
7. Verify the action landed (re-read your own sent record; an agent must never
   verify its own work from memory): …
8. Persist state, append log, exit.

## 4. Stop conditions

When the loop stops iterating on its own, and what it does then (submit?
report? wait?). Include the round's "nothing left to do" definition and the
one-shot exam timing decision.

---

# State vs. log conventions

Keep these two things physically separate. The loop reads STATE to decide;
it appends to LOG to explain. Never reconstruct state by re-reading the log.

**`state.*` (durable, mutable, small — the loop's memory):**
- one record per supplier per round: contacted? quote received (email id)?
  extracted values, validation verdicts, action taken, escalation email id,
  approver ruling, reminder sent (sim time), pushback status
- `last_seen_sim_time`, current round id, exam started?
- overwritten in place; must survive a process restart; readable by a human
  (JSON/YAML/SQLite are all fine)

**`log.*` (append-only, immutable — the loop's history):**
- one line per action with sim time AND wall-clock time: what was read, what
  was decided and why, what was sent (email id), what changed in state
- errors and retries
- never edited, never truncated

**Rule of thumb:** if deleting the file would make the loop re-do work it
already did, it is state. If deleting it would only lose the explanation, it
is log. Your loop must never re-ask what state already knows and must never
double-email a supplier — both are measured server-side.
