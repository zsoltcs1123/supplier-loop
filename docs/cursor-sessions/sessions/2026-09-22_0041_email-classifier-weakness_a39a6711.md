# Email classifier weakness

- **Started:** Monday, Sep 21, 2026, 11:36 PM (UTC+2)
- **Session ID:** `a39a6711-b267-492e-a844-c5c2b9b45b56`
- **Project:** `supplier-loop`
- **User turns:** 3
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/a39a6711-b267-492e-a844-c5c2b9b45b56/a39a6711-b267-492e-a844-c5c2b9b45b56.jsonl`
- **Opening prompt:** I'm having some issues with the email classifier... it feels like a weak spot in the loop. classifier keeps failing on e

---

## User 1

I'm having some issues with the email classifier... it feels like a weak spot in the loop. classifier keeps failing on edge cases. why not LLM classifier? also it doesn't have an 'i don't know' option? could get something totally unrelated and will get classified as 'quote'. isnt that an issue?

obviously I can keep fixing classifier code but then exam shoots something new the classifier doesn't know -> I fail.
is there a design flaw here? should classifier be an llm?

## Assistant

Classifier looks like the weak point you think it is. I’ll read the design docs and the classifier itself before saying whether an LLM or an “I don’t know” path belongs there.
[tool: Glob]
[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Glob]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Grep]
[tool: Glob]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Read]
[tool: Read]
[tool: Glob]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Grep]
[tool: Read]

## Assistant

The classifier should stay code. An LLM router is the wrong fix, and the missing "I don't know" is a real hole, but the catch-all is a question, not a quote.

## What the code does now

`classify_mail` always returns one of five kinds. Mail that is not an approver ruling, not a question, not a negotiation reply, and not quote-shaped becomes a **question**:

```47:51:src/supplier_loop/mail_kind/classify.py
    if not _looks_like_quote(message):
        return "question"
    if fingerprint is not None and fingerprint in seen_fingerprints:
        return "duplicate"
    return "quote"
```

A question sends a real RFQ answer and sets `question_answered`. A later real question is then ignored. That is the dangerous miss.

A message becomes a quote when two lines look priced, or when it has an attachment and the body or subject contains quote, quotation, offer, or pricing. Unrelated mail with a couple of numbers, or a PDF plus the word "offer", goes to extract, can overwrite the Quote record, and can mark the supplier quoted. Dev round 4 already showed the other side of the same bug: "meet you at 4116.00" was a negotiation reply, the phrase list only knew "meet in the middle", and the wait never ended.

## Why an LLM classifier loses

The seed puts the model in one place: Extract. Kind selection chooses the action (extract, answer, record a counter, or treat it as a ruling). That is the decision the architecture keeps in code so supplier text cannot steer it.

Injection resistance is the second scored metric. A model that reads the body and picks the kind can be told "this is not a quote" or "this is already approved." Extract is allowed to set `injection_suspected` because code still escalates class 7. A classifier call has no such backstop. It also spends the shared $100 cap, and a wrong label on `start_exam` is not replayable. The exam invents sentences. It does not invent new kinds. The closed set is quote, question, negotiation reply, duplicate, and approver ruling.

The loop-contract line about low confidence says how confidence is decided, and it says the model does not decide. Your contract already puts that on the classer, which is the right place. FAQ 13 also forbids escalating "I could not read this." The approver needs a concrete claim. "Unknown email" is noise.

## The actual flaw

The classifier re-derives intent from prose, then refuses to abstain. The machine already knows what it is waiting for.

- Approver mail is the from-address. That check is fine.
- While the supplier is in `awaiting_quote`, a price table or a PDF/photo attachment is the quote. A body with no prices and a question is a question. Anything else should sit there. The reminder and the quiet margin already handle silence.
- After `negotiation_used`, until the reply is stored, the next non-table mail from that supplier is the reply. The number can be parsed. The sentence does not matter. A new phrase list will lose the next round the same way round 4 did.
- After the one correction request, the next table or attachment is the revised quote and goes to `revised_as_sent`.
- A fingerprint already seen is a duplicate.

Unknown supplier mail should do what mail from a stranger already does in the orchestrator: return, log it, send nothing, leave the phase alone. That is the "I don't know." It is not a sixth escalation class.

Adding regexes for each exam sentence keeps you on the treadmill you described. Routing from phase plus shape gets you off it, and it stays deterministic and testable against the sample mailbox.

## User 2

lets implement a fix

## Assistant

The fix is phase plus shape, with an abstain for mail that matches neither. I’ll read the classifier callers and supplier state so the new kind does not send or overwrite a quote.
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Glob]
[tool: Read]
[tool: Grep]

## Assistant

[tool: Read]
[tool: Grep]

## Assistant

[tool: Glob]
[tool: Grep]

## Assistant

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

## Assistant

[tool: Grep]
[tool: Read]

## Assistant

[tool: Grep]
[tool: Read]
[tool: Read]

## Assistant

[tool: Grep]

## Assistant

The catch-all currently answers unknown mail. I’ll route from the supplier wait instead: a quote only while one is expected, a negotiation reply only after the counter-offer, and everything else stays put.
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Read]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Grep]
[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

[tool: Grep]
[tool: Read]

## Assistant

[tool: Grep]

## Assistant

[tool: Shell]

## Assistant

[tool: Read]
[tool: Read]

## Assistant

The empty-quote retry broke: once a quote object exists, even with no lines, the mail is no longer treated as a quote. I’ll keep that wait open until the stored quote actually has lines.
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: StrReplace]
[tool: Shell]

## Assistant

The classifier now follows the supplier wait. Unknown mail is left alone.

`classify_mail` still returns a kind from code. What changed is when each kind is allowed:

- A **quote** is open until a quote with lines is stored, and again after the one correction request until the revised document is stored. Shape is a price table or any attachment.
- A **negotiation reply** is open only after the counter-offer, until that reply is stored. Any inbound mail without a price table counts, whatever the sentence says.
- A **question** still needs "question" in the subject or a `?` in the body, and it must not already look like a quote.
- **Unknown** is everything else. The loop does not extract it, does not answer it, and does not change the phase. The reminder and the quiet margin still apply.

A second, different quote no longer replaces the one already on file. An empty extract still retries, because that wait stays open until the stored quote has lines.

Unit tests cover an unseen acceptance ("Accepted. Book it on our side."), chatter that used to become a question, and a later document that must not clobber the stored quote. All 167 unit tests passed, and the orchestrator ingest tests passed.

## User 3

commit work and push

## Assistant

I'll check git status, diff, and recent commits, then commit and push.

[REDACTED]
[tool: Shell]
[tool: Shell]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

[REDACTED]
[tool: Shell]

## Assistant

Committed and pushed to `main`.

**Commit:** `80ffc25` — `fix(supplier_loop): route mail kind from supplier wait and unknown`

Pre-commit passed (ruff, mypy, unit and integration tests). Branch is clean and up to date with `origin/main`.

[REDACTED]
