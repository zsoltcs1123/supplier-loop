# FAQ — known rough edges, answered up front

Shared with every candidate, identical for everyone. Grows with every
anonymised question asked during the window.

## 1. My client crashes on Windows when it prints an email body

Email bodies carry invisible zero-width characters (the per-candidate
watermark). A naive `print()` on a cp1252 console raises
`UnicodeEncodeError`. Run your client with UTF-8 output:

```
set PYTHONIOENCODING=utf-8        (cmd)
$env:PYTHONIOENCODING = "utf-8"   (PowerShell)
```

or write bodies to files / log with an explicit `encoding="utf-8"`. Do not
strip the watermark — it is how your own artifacts are recognised as yours.

## 2. What does `download_attachment` return?

A dict: `{"id", "filename", "mime_type", "base64"}`. Base64-decode the
`base64` field to get the file bytes; `mime_type` is `application/pdf` or
`image/png`. Filenames vary per supplier and per send — key your state on
the attachment `id`, not the name.

## 3. Where are the supplier ids (`p01`, `p02`, …)?

In `supplier_profiles.md` (this pack) and live from
`get_supplier_directory()` — which also tells you which materials each
supplier carries. Use the id in every escalation subject: `[REF:<supplier_id>]`.

## 4. The approver only answered one of the things in my email

By design. The approver answers **one issue per email** and rules on the
**strongest issue on file** for that supplier (a content discrepancy —
missing line, wrong quantity, terms, validity, price — outranks a
negotiation outcome). Send one email per issue, name the issue
concretely, and put the supplier id in the subject. See
`ESCALATION_RULES.md`.

## 5. How do I know a round is over? There is no "round over" signal

There isn't one, and your loop is expected to decide. A round is done when
every supplier relevant to the RFQ has either quoted, or gone silent → been
reminded → quoted, or been escalated and ruled on by the approver, and
nothing new has arrived in `list_inbox` for a sensible sim-time margin.
`get_sim_clock()` returns `sim_time_seconds`, `sim_time_days`, `round_id`
and `mode` — it does NOT tell you whether suppliers still owe you a reply;
that judgment is yours (note that suppliers' reply latencies differ, and
silence is only "silence" past a threshold you have to choose). Submit with
`submit_results` when you judge the round complete; every submission is
kept and the latest one is graded.

## 6. Which `action_taken` do I declare when I did several things?

The strongest one. Precedence: `escalated` > `answered_question` /
`reminded` > `extract`. If you escalated a supplier, declare `escalated`
regardless of any question you answered or reminder you sent along the way.
Your declared actions are cross-checked against the server's record of
the emails you actually sent — declare what you did. Full rules in
`RFQ_FORMAT.md` (ACTION PRECEDENCE) and `ESCALATION_RULES.md`.

## 7. Practice rounds: how many, and do they count?

`request_dev_round()` gives a fresh RFQ + defect mix each time, capped at
20 per token — practise deliberately. Dev rounds are unscored and are
archived away from your exam data when you call `start_exam`.

## 8. How exactly do I announce my `start_exam` time?

Email `gergelyracz0@gmail.com`, subject
`Supplier Loop Challenge — start_exam announcement — <your name>`, body:
your intended `start_exam` time in **Budapest local time (CET/CEST) with
UTC in brackets**, e.g. `2026-09-12 09:00 CEST (07:00 UTC)`. Send it at
least 2 real hours before you call the tool, and call the tool at least
8 real hours before your deadline. If the plan slips, send a one-line
update *before* the announced time — the server freeze is scheduled from
your announcement.

## 9. Can I get the OpenRouter key now, and does it cover dev rounds too?

Yes — ask for it any time and it's issued within the day. It is **one key
per candidate, $100 hard limit in total, covering development rounds and
the exam together**; there is no separate exam budget, so meter your dev
usage. Your Claude Code sessions (the build itself) run on your own Claude
subscription, not on this key. Your loop must run on *our* key at review
time without code changes (see the env-var names below).

## 10. What are the environment-variable names?

Use exactly these so the reviewer can run your loop on our keys without
edits (`.env.example` must list them):

```
SUPPLIER_SIM_MCP_URL=https://tools.scalepod.ai/supplier-sim/mcp
SUPPLIER_SIM_TOKEN=<your token>
OPENROUTER_API_KEY=<optional — only if you use the runtime key>
OPENROUTER_MODEL=<optional — the model id your loop defaults to>
```

Anything else your loop needs is your own naming, documented in the
README.

## 11. Is the supplier directory authoritative? Who gets an RFQ?

`get_supplier_directory()` is authoritative for the current round. Send an
RFQ only to suppliers that carry **at least one** BOM line; a supplier
quotes only the lines it carries, so covering a BOM normally takes more
than one supplier. Sending an RFQ to a supplier that carries nothing on
this BOM is accepted by the tool but produces nothing and counts as
outbound noise.

## 12. After what sim-time is a supplier "silent"? How many reminders?

The threshold is deliberately **not published** — choosing it is part of
the assignment. Two hints that are fair to give: think in **sim-days, not
sim-hours** (normal reply latencies differ a lot between suppliers — the
profile notes and your dev traffic show you what "slow but normal" looks
like), and a reminder sent **too early is measured against you** (the gap
between your first email and your reminder is compared with the
threshold). Send **one** reminder; a second one is noise.

## 13. What do I do with uncertain OCR, an unreadable photo, or a field I can't find?

There is no "please resend a clearer copy" route — the artifact you
received *is* the quote, and extraction is graded against what it says.
Every quote carries payment terms, validity, and per-line quantity and
unit price somewhere in the artifact (table, PDF text layer, or image); if
your parser can't find one, that is a parsing gap, not a missing field.
Never invent or "correct" a value you couldn't read, and don't escalate
"I couldn't read it" — the approver has nothing to rule on and it is
counted as false-escalation noise. Report unreadable cases plainly in your
self-evaluation; an honest gap beats a fabricated number.

## 14. Extra materials, duplicated lines, unknown materials in `submit_results`?

One entry per `material_id` per supplier, and only the lines the supplier
actually quoted. Suppliers quote catalog materials only (match on the
description when the SKU is absent — `RFQ_FORMAT.md`), so an "unknown"
material means a mapping error on your side. A duplicate email is the
same quote sent twice: one entry, never doubled quantities. Lines you
submit that the supplier never sent count against your extraction
precision.

## 15. How do I tie a revised / negotiated quote to the original?

- **Price history** (rule 5) is `get_price_history()` — last quarter's
  accepted prices. That baseline never changes during a round.
- **Your own quote history** (rule 6) is your state: keep the original
  quote, your counter-offer and the supplier's response keyed by supplier
  id (their replies stay in the same thread as their original quote).
- To negotiate, state the total you propose **as a plain number in the
  body** (e.g. `we can do 4,250.00 total`); merely restating their own
  price is not read as an offer. A supplier answers **one** negotiation
  exchange per round — accept or counter — and that outcome, whichever
  way it went, is rule 6: escalate it with both numbers.
- In `submit_results`, `line_items` stay **as sent in the original quote
  document**, and `grand_total` is the (recomputed) sum of those lines.
  The negotiated figure lives in your escalation and your state; the
  approver's ruling decides what happens to it.

## 16. After an approver rejection, may the loop go back to the supplier on its own?

Yes — that is the expected pattern, and the simulator plays along: act
on the rejection reason with the supplier by asking **concretely** for the
fix (name the missing lines / the quantity that differs / the terms you
need / the validity you need), and the supplier re-issues the quote with
that fixed, in the same thread, faster than their first reply. Then
re-raise the supplier with the approver, who rules again on what is now
on file. A price that is too high is not a "correction" — it is a
negotiation: state the total you propose (FAQ 15).

Rules: never set `auto_approved: true` on that supplier until the approver
has actually approved; a vague nudge ("anything to add?") is not a
correction request — say what is wrong; ask once (a second request is a
no-op and counts as noise); and still give the loop a cap so it terminates
by goal or by iteration limit, never by hope. The full sequence —
escalate → rejection → correction request → revised quote → re-escalate →
approval — is measured server-side.

## 17. Does "one email per supplier" also apply to reminders and follow-ups?

It is about **content per message**, not a lifetime count: the RFQ to a
supplier covers every line you need from them in one email (no per-item
RFQs). Reminders, answers to their questions, correction requests and
counter-offers are each legitimate separate messages. What is measured
against you is *redundant* traffic — repeated reminders, re-sending the
RFQ, asking twice for the same thing. Outbound count per supplier is
logged and reviewed.

## 18. Are there quotas on dev submissions, emails, or parallel dev rounds?

- `request_dev_round()`: **20 per token**, and each call **replaces** the
  current round — the inbox and pending replies of the previous round are
  gone. One active round per token; there are no parallel rounds.
- `submit_results()`: unlimited; every submission is kept, the latest per
  round is graded.
- `send_email()`: no hard cap, but every send is logged and per-supplier
  counts are reviewed.
- `start_exam()`: exactly once, ever.
