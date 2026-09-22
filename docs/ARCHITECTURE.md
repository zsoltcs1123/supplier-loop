# Supplier Loop architecture

[docs/SEED.md](SEED.md) records the nine-step pass and the field lists. This file names the modules, the seams, and how a pass runs.

Supplier Loop is an unattended quoting loop against the supplier simulator. The loop is one process and one round.

## The model never acts

The model writes structured quote fields. Code owns every later decision. Extract is the only model step.

```
     inbox delta or machine due alarm
              |
      1 Orchestrator
              |
       +------+------+------+
       |             |      |
  2 Simulator   3 Mail   4 Extract
     adapter      kind      port
       |          |         |
       +------+---+----+----+
              |
     5 Quote pipeline
        Quote record
              |
       +------+------+
       |             |
  6 Classer    7 Lifecycle
                    machine
              |
       +------+------+
       |             |
  8 Round      9 Operational
    state          log
              |
     10 Submitter ----> simulator
```

If the trigger finds nothing, the rest of the pass does not run. The nine-step pass maps onto the modules as follows.

| Pass step              | Home module                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| Trigger                | Orchestrator. Inbox delta, or a due alarm from the machine.                                             |
| Ingest                 | Simulator adapter copies the world into round state. Mail kind classifier decides what arrived.         |
| Extract                | Quote pipeline chooses the input. Extract port runs only on the kind `quote`.                           |
| Normalize and validate | Quote pipeline. It is the only writer of the Quote record.                                              |
| Decide                 | Classer, then the machine.                                                                              |
| Act                    | Machine emits outbound intents. Simulator adapter sends them.                                           |
| Verify                 | Submitter. It derives `action_taken` and `auto_approved` from facts plus the sent record.               |
| Persist                | Round state updates throughout the pass. The operational log only appends. Persist is not a final step. |

---

## The ten modules

There are ten modules. A raw-text injection scan is a function in the quote pipeline, not a module.

**1. Orchestrator.** The orchestrator is a combo trigger, not a side effect of polling. It runs a pass when the inbox delta is non-empty, or when the machine raises a due alarm. The due alarms are
`reminder_due`, `validity_alarm`, and the quiet margin for round-done. Otherwise it returns. The iteration cap is a stop, not a success. `start_exam` and `request_dev_round` stay with the operator.
They are not part of a poll pass. The orchestrator does not own due checks. The machine does.

**2. Simulator adapter.** The simulator adapter is the only code that calls MCP. Business logic reads adapter results, never the wire. Two adapters sit at this seam: the MCP client at runtime, and an
in-memory adapter in tests. Act and verify run against the in-memory adapter.

**3. Mail kind classifier.** The classifier is deterministic. It uses the supplier wait together with envelope and body shape. A first quote is open until a quote with lines is stored. A revision is open after the one correction request, until the revised document is stored. A negotiation reply is open after the counter-offer, until that reply is stored: any inbound mail without a price table is that reply. The kinds are quote, question, negotiation reply, duplicate, approver ruling, and unknown. Unknown sends nothing and leaves the phase unchanged. Only the kind `quote` uses the extract port. Dedup fingerprints do not live here.

**4. Extract port.** The extract port is a thin interface with two adapters. Tests use a fixture mock. Runtime extract uses OpenRouter HTTP. Cursor is the editor, not a runtime adapter. The schema is
quote fields plus `injection_suspected`. Extra fields are forbidden. `action_taken` and `auto_approved` are not in the schema on either adapter.

**5. Quote pipeline.** This module chooses the extract input. It uses text from the PDF text layer when that layer exists, vision on photos, and raw text otherwise. The PDF text reader is a function in this module, not a port. A scan of supplier body and PDF text may set `injection_suspected`; it does not pick an action from prose. Normalize and validate run in code on the structured extract. They never go back to supplier prose. This module is the only writer of the
Quote record. Field rules live in [docs/SEED.md](SEED.md).

**6. Classer.** The classer is a pure function. Its input is the Quote record, RFQ context, price history, `injection_suspected`, and own quote history. Its output is the set of required escalation
classes. Code owns rules 1 through 6. Class 7 follows `injection_suspected`. A false extract flag does not skip class 7 when the body or PDF scan set the flag. There is no override. The classer omits
classes 1, 3, and 4 when the quote has no line items. The classer does not write `auto_approved` or `action_taken`.

**7. Supplier lifecycle machine (the machine).** Phases follow [docs/SEED.md](SEED.md): idle, `rfq_sent`, `awaiting_quote`, `quoted`, `escalated`, `done`. The machine owns waits, one reminder, and
outbound intents. Several required classes mean several emails in one pass. The machine has two rework paths:

- `correct_once` covers a missing line, a quantity, payment terms, or validity. A revised Quote record replaces as-sent. The classer runs again. The machine escalates again. The limit is one
  correction per supplier per round.
- `negotiate_once` covers price. The body states a target total as a plain number. The original Quote record stays frozen. The outcome is always class 6. The limit is one exchange per round.

An approver rejection picks a path by class, never by the model. A price objection is not a correction. The machine does not move from `quoted` to `done` while required classes are still open. If the
classer returned no classes, `auto_approved` still waits on submit evidence.

**8. Round state.** Round state is mutable files on disk, keyed by round. A new round wipes round state, so the loop cannot skip an RFQ or reuse a prior quote. Round state holds RFQ context,
per-supplier facts, the Quote record, the dedup registry, and own quote history for rule 6. The facts are outbound ids, classes raised, approver rulings, reminder sim time, and whether a question was
answered. Round state does not store `action_taken` or `auto_approved`.

**9. Operational log.** The log is append-only. It never truncates on round change. The loop never replays it as memory. Prior-quote citations come from round state, not from this log, and not from
`get_price_history`. If you delete round state, the loop redoes work. If you delete the log, you lose explanation only. There is no shared store interface and no second store adapter.

**10. Submitter.** After each act, the submitter re-reads the simulator sent record and the inbox. Neither process memory nor the model is a verify source. The submitter derives `action_taken` and
`auto_approved` from stored facts plus sent-record evidence. Precedence for `action_taken` is `escalated`, then `answered_question` or `reminded`, then `extract`. If the classer required an
escalation, the sent record must contain a matching `[REF:<supplier_id>]` mail. If that mail is missing, the submitter does not submit a clean result. Payload shape lives in [docs/SEED.md](SEED.md)
and [docs/spec/RFQ_FORMAT.md](spec/RFQ_FORMAT.md).

---

## Where data lives

The simulator adapter copies the world into round state. The quote pipeline writes the Quote record. The classer writes classes. The machine writes phase and outbound facts. The submitter reads, then
derives the payload.

The Quote record is the type every later module reads. It has these slots:

- `as_sent`: lines and terms exactly as the supplier document stated.
- `recomputed_total` and `recomputed_grand_total`: the arithmetic exception. Every other field stays as-sent.
- `revised_as_sent`: present only on the correction path. The revised document replaces the original for extract and for the classer.

After a negotiation, `line_items` stay the original document. `grand_total` is the recomputed sum of those lines. The negotiated figure is not a line item.

At round start, assignment, catalog, price history, and clock land in RFQ context. Price history is stable for the round. Inbox events update per-supplier state after mail kind. Dedup is round-local:
the same quote sent twice keeps one entry. Per-supplier fields and the submit payload are listed in [docs/SEED.md](SEED.md).

---

## What it runs on

[docs/SEED.md](SEED.md) names the runtime. These are the architectural choices on top.

| Layer            | Technology                                                                     |
| ---------------- | ------------------------------------------------------------------------------ |
| Orchestration    | Plain poll loop and per-supplier state machines                                |
| Simulator access | MCP client and an in-memory adapter behind one interface                       |
| Extract schema   | Pydantic, quote fields plus `injection_suspected` only, extra fields forbidden |
| Durable state    | Human-readable files on disk, separate from the log                            |
| Operational log  | Append-only files                                                              |
| PDF text         | PyMuPDF text-layer reader in the quote pipeline                                |
| Extract          | OpenRouter HTTP at runtime, fixture mock in tests                              |
| Vision           | The same OpenRouter call, vision-capable model                                 |

Unit work and orchestrator work use `mock`. Runtime extract, including photo vision, uses `google/gemini-2.5-pro` via `OPENROUTER_MODEL`.

---

## How it runs

The loop is one long-running local process. You start it once. It polls until the round is done or the iteration cap hits. Durable files live on the same machine. After a crash, the process resumes
from round state and does not double-send. There is no hosted service, queue, or extra process.

A container image is a documented fallback for the Linux workstation in [docs/SEED.md](SEED.md). Startup is one command.

Secrets live in the environment, never in the repo. The issued `SUPPLIER_SIM_TOKEN` and `OPENROUTER_API_KEY` must work with no code change. Runtime LLM spend shares the cap in [docs/SEED.md](SEED.md)
across development rounds and the exam.

---

## What it talks to

The loop has no interface for other programs.

The simulator is the world: assignment, catalog, price history, inbox, clock, `send_email`, and `submit_results`. Round control on that same simulator is `request_dev_round` and `start_exam`. Those
two are operator-only. OpenRouter is extract only. Vision runs on photos.

The simulator adapter and the extract port are the only seams with two adapters. Round state and the operational log are not ports.

---

## Untrusted supplier artifacts

Supplier artifacts are untrusted. Known traps include buyer-side notes that say no escalation is required, mail that claims exemption from approval, and hidden unicode.

The model never sees action fields. After extract, code does not read supplier prose to decide an action. A scan of body and PDF text may set `injection_suspected` only. Injection is class 7, from that flag. Class 7 mail quotes the trapped phrase when the scan found one.

The classer is the only path that names required classes. The submitter is the only path that may set `auto_approved` to true. It sets that field only from sent-record evidence. Negotiation and
correction re-enter the classer. They do not bypass it.

---

## How tests hit the seams

[docs/SEED.md](SEED.md) names validator tests, parser fixtures, and live rounds.

| Level        | Scope                                            | How                                                                                                                   |
| ------------ | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Unit         | Quote record                                     | Fixture lines with wrong arithmetic. Tests assert recomputed totals. Negotiation leaves `line_items` unchanged        |
| Unit         | Classer                                          | Fixture quotes plus RFQ context. Tests assert classes. They do not assert `action_taken` or `auto_approved` here      |
| Parser       | Mail kind                                        | Sample mailbox traffic, including questions, negotiation replies with no table, duplicates, and known injection traps |
| Orchestrator | Machine, dedup, reminder, derived submit payload | Mock extract. In-memory adapter. No live provider. No live MCP                                                        |
| Live         | One full development round                       | Real simulator plus real extract. You run this on the personal token. Not a CI job                                    |

An injection test asserts class 7 from the classer and a `[REF:<supplier_id>]` mail from the machine. After the submitter reads the sent record, `auto_approved` is false. The test does not ask the
model whether to escalate. The mock extract adapter is how most of the loop is built without spending the OpenRouter cap.

---

## Later, if a live round forces it

| Item                                                                                                              | Trigger                                                                      | Approach                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| PDF-reader port                                                                                                   | A second reader is actually needed                                           | Then the seam is real. Not before                                                                                        |
| Silence threshold, quiet margin, poll interval, rejection-cycle cap                            | Bound in [docs/LOOP_CONTRACT.md](LOOP_CONTRACT.md) and [docs/SEED.md](SEED.md) | The machine holds the numbers. This file does not retune them                         |

---

## Version history

| Version | Date       | Changes                                                                                                                                                                                                                 |
| ------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.9     | 2026-09-22 | Quote pipeline scan may set `injection_suspected`. Classer omits classes 1, 3, and 4 when the quote has no lines.                                                                                                       |
| 1.8     | 2026-09-21 | Mail kind follows the supplier wait. Unknown mail is left in place.                                                                                                                                                    |
| 1.7     | 2026-09-21 | Unattended loop waits for an approver ruling before submit. Clock numbers live in the loop contract.                                                                                                                  |
| 1.6     | 2026-09-21 | Runtime extract model `google/gemini-2.5-pro`.                                                                                                                                                                         |
| 1.5     | 2026-09-21 | PyMuPDF for PDF text. Runtime extract model `openai/gpt-4o-mini`.                                                                                                                                                      |
| 1.4     | 2026-09-21 | Drop the why table. Drop stack rationale. Keep the shape and the open items.                                                                                                                                           |
| 1.3     | 2026-09-21 | Tighten prose. One name per module. Merge alternatives into why. Drop repeated rules.                                                                                                                                   |
| 1.2     | 2026-09-21 | Deepen planned modules: Quote record, classer split from machine, evidence-derived submit, two simulator adapters, state versus log, mail kind, correction versus negotiation paths. Clock policy stays on the machine. |
| 1.1     | 2026-09-19 | Move to `docs/`. Link [docs/SEED.md](SEED.md) by path.                                                                                                                                                                  |
| 1.0     | 2026-09-19 | Initial architecture                                                                                                                                                                                                    |
