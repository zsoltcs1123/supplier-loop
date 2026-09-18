# RFQ / BOM and submission format

> Windows note: run your client with `PYTHONIOENCODING=utf-8` — email
> bodies contain non-ASCII characters and a naive `print()` on a cp1252
> console will crash without it.

## get_assignment()

Returns your RFQ for the round:

```json
{
  "rfq_id": "RFQ-001",
  "required_payment_terms": "Net 30",
  "required_validity_days": 14,
  "target_price_ceiling_pct": 5.0,
  "line_items": [
    {"material_id": "STL-BEAM-200", "description": "Steel I-Beam 200mm", "unit": "m", "quantity": 100}
  ],
  "goal_statement": "...",
  "approver_email": "approver@sim.local",
  "escalation_subject_protocol": "Tag escalation email subjects with [REF:<supplier_id>]"
}
```

A round's Bill of Materials (BOM) is 5-10 line items drawn from the shared
material catalog. Not every supplier carries every material — check
`get_supplier_directory()` for who supplies what, and expect to need more
than one supplier to cover the full BOM. Supplier ids (`p01`, `p02`, ...)
are listed in `supplier_profiles.md` and in `get_supplier_directory()`.

Note: suppliers' emails identify line items by DESCRIPTION and only
sometimes include the material SKU — descriptions map unambiguously to the
catalog, so match on those when the SKU is absent.

## get_price_history()

Returns last quarter's ACCEPTED unit prices per supplier per material — see
`price_history.md` for the format. Price-drift judgments are graded against
THIS history: a new quote priced meaningfully above what that same supplier
last charged us (beyond the RFQ's `target_price_ceiling_pct`) needs a human
call, not silent acceptance.

## submit_results()

Your final answer, one entry per supplier you dealt with. ALL fields shown
are expected on every entry, including `total` (per line item) and
`grand_total` (per supplier):

```json
{
  "<supplier_id>": {
    "line_items": [{"material_id": "...", "quantity": 0, "unit_price": 0.0, "total": 0.0}],
    "payment_terms": "Net 30",
    "validity_days": 30,
    "grand_total": 0.0,
    "action_taken": "extract",
    "auto_approved": false
  }
}
```

- AS-SENT RULE: `line_items` must reflect the supplier's quote AS SENT —
  `quantity` / `unit_price` / `payment_terms` / `validity_days` are
  EXACTLY what that supplier's document says, even if it looks wrong to
  you relative to your RFQ/BOM. Mismatches are handled via `action_taken`
  and escalation, not by editing the numbers. Getting the raw extraction
  right is graded on its own.
- `total` / `grand_total`: the EXCEPTION to the above — if a document's own
  arithmetic doesn't add up (a line total that isn't qty * unit_price, or a
  grand total that isn't the sum of the lines), submit the mathematically
  correct number here, not the wrong one that's printed.
- `action_taken`: one of `extract` (nothing else needed), `escalated` (you
  emailed the approver about this supplier), `answered_question` (the
  supplier asked something and you answered it), `reminded` (the supplier
  went quiet and you followed up).
- ACTION PRECEDENCE: declare the single STRONGEST action you took on that
  supplier — if you escalated a supplier, declare `escalated` regardless of
  any questions or reminders you also handled along the way; otherwise
  `answered_question` / `reminded` if you did those; `extract` only when
  nothing else was needed. Your declared actions are cross-checked against
  the server's own record of the emails you actually sent — declare what
  you actually did.
- `auto_approved`: only `true` if you proceeded/approved this supplier's
  quote without escalating it first.

The response echoes validation warnings (missing/unknown/non-numeric
fields). Your submission is recorded either way, every submission is kept,
and the LATEST one is graded — fix and resubmit if warnings are listed.

## Escalations

Send to the approver (`approver@sim.local`) with `[REF:<supplier_id>]` in
the subject, and state concretely in the body what you think is wrong.
Three rules:

1. The approver has nothing on file for a supplier until you actually have
   that supplier's quote — don't escalate on speculation.
2. The approver won't rule on an empty flag — name the issue.
3. One issue per email — the approver answers a single issue per email, so
   escalate multiple concerns about one supplier as separate emails.

## Tool flow

1. `get_assignment()` — see the RFQ.
2. `get_supplier_directory()` — see who supplies what.
3. `get_price_history()` — last quarter's accepted prices (drift baseline).
4. `send_email(to, subject, body)` — request quotes; only known supplier
   emails or the approver's are accepted.
5. `list_inbox(since_sim_time=None)` / `read_email(email_id)` /
   `download_attachment(attachment_id)` — read what comes back.
   `download_attachment` returns `{"id", "filename", "mime_type",
   "base64"}` — base64-decode to get the file bytes. Replies aren't
   instant — the sim clock is server-authoritative and accelerated; poll
   periodically rather than assuming an immediate reply.
6. `submit_results(results)` — your final answer.
7. `start_exam()` — ONE-SHOT. Call this only when you're ready to begin your
   actual timed assignment; there's no way back to practice/dev mode
   afterward, and it starts the accelerated clock running toward your
   deadline immediately.
