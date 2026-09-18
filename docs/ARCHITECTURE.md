# Supplier Loop architecture

[docs/SEED.md](SEED.md) records the loop pass, the field lists, and the locked decisions. This file names the components, the trust boundary, and how the process runs.

Supplier Loop is an unattended quoting loop against the supplier simulator. One process, one round. Extract is the only model step because the server scores escalation and injection first, and because the exam runs for hours without you.

**Core principle:** The model writes structured quote fields. Code owns every later decision. The model never acts.

```
     sim clock or inbox delta
              |
      1 Orchestrator
              |
       +------+------+
       |             |
  2 Simulator     3 LLM extract
     adapter           port
       |             |
       +------+------+
              |
     4 Quote pipeline
              |
   5 Escalation router and
     supplier state machines
              |
      6 Durable store
              |
      7 Submitter ----> simulator
```

The nine-step pass in [docs/SEED.md](SEED.md) maps onto these components. If the trigger finds nothing, the rest of the pass does not run.

---

## Components and responsibilities

The system has seven components. A backup injection heuristic is optional and is not one of them.

**1. Orchestrator.** The orchestrator is a combo trigger, not an implied side effect of polling. It watches sim-clock events and inbox delta, then either runs a pass or returns. Iteration cap is a stop, not a success. `start_exam` and `request_dev_round` stay with the operator. They are not part of a poll pass.

**2. Simulator adapter.** The only code that calls MCP. Business logic reads adapter results, never the wire.

**3. LLM extract port.** A thin interface with two backends. Tests use a fixture mock. Runtime extract uses OpenRouter HTTP. Cursor is the editor, not a runtime backend. The schema is quote fields plus `injection_suspected`. Action fields, `auto_approved`, and `action_taken` are not in that schema, on either backend.

**4. Quote pipeline.** Extract is the only model step. This component chooses the input: code-read PDF text when a text layer exists, vision on photos, raw text otherwise. Normalize and validate run in code on that structured extract. They never go back to supplier prose. Field rules live in [docs/SEED.md](SEED.md).

**5. Escalation router and supplier state machines.** The router runs after validate. Code owns rules 1 through 6. Class 7 follows `injection_suspected`. Phases follow [docs/SEED.md](SEED.md). The architectural gate is this: the machine cannot move from `quoted` to `done` with `auto_approved` true until the router is clear, or until every required class is escalated and the approver has ruled.

**6. Durable store.** Round-keyed files on disk. A new round wipes mutable state so the loop cannot skip an RFQ or reuse a prior quote. The append-only log may continue. The loop does not replay it.

**7. Submitter.** After each act, the verify step re-reads the simulator sent record and the inbox. The submitter then builds `submit_results` from persisted per-supplier state. Process memory and the model are not sources. Payload shape and `action_taken` rules live in [docs/SEED.md](SEED.md) and [docs/spec/RFQ_FORMAT.md](spec/RFQ_FORMAT.md).

**Optional later.** A backup heuristic scan of raw supplier text, for instruction-like phrases and hidden unicode. This scan is out of scope for the first milestone. Placement next to extract or inside the router is still open.

---

## Data architecture

The adapter copies the world into round state. The pipeline and the router update per-supplier records. `submit_results` only reads.

At round start, assignment, catalog, price history, and clock land in RFQ context. Price history is stable for the round. Inbox events update per-supplier state. Dedup is round-local: the same quote sent twice keeps one entry. Per-supplier fields and the submit payload are listed in [docs/SEED.md](SEED.md).

The operational log is an audit trail. Prior-quote citations for the history rule come from per-supplier state in the current round, not from that log, and not from `get_price_history`.

---

## Technology stack

[docs/SEED.md](SEED.md) names the runtime. These are the architectural choices on top.

| Layer | Technology | Rationale |
| --- | --- | --- |
| Orchestration | Plain poll loop and per-supplier state machines | Decisions stay in code |
| Simulator access | MCP client behind the adapter | MCP calls stay out of business logic |
| Extract schema | Pydantic, quote fields plus `injection_suspected` only | The model cannot return an action |
| Durable state | Human-readable files on disk | Survives a restart, inspectable, wiped on round change |
| PDF text | Text-layer reader, library still open | Code first. The model runs only when the PDF has no usable text |
| LLM extract | OpenRouter HTTP at runtime, fixture mock in tests | One issued key. Most build work makes no OpenRouter call |
| Vision | The same OpenRouter call, vision-capable model | Photos and screenshots only |

The backends are `mock` and OpenRouter. Unit and orchestrator work use `mock`. Plumbing smoke uses a cheap vision-capable model. Pre-exam tune uses a stronger model. The exam model id stays open in [docs/SEED.md](SEED.md).

---

## Infrastructure and deployment

The loop is one long-running local process. You start it once. It polls until the round is done or the iteration cap hits. Durable files live on the same machine. After a crash, the process resumes from those files and does not double-send. There is no hosted service, queue, or extra process.

A container image is a documented fallback for the Linux workstation in [docs/SEED.md](SEED.md). Startup is one command.

Secrets live in the environment, never in the repo. The issued `SUPPLIER_SIM_TOKEN` and `OPENROUTER_API_KEY` must work with no code change. Runtime LLM spend shares the cap in [docs/SEED.md](SEED.md) across development rounds and the exam.

---

## APIs and integrations

The loop exposes no API of its own.

The simulator is the world: assignment, catalog, price history, inbox, clock, `send_email`, and `submit_results`. Round control on that same simulator is `request_dev_round` and `start_exam`. Those two are operator-only. OpenRouter is extract only. Vision runs on photos.

Internal ports: the simulator adapter, and the LLM extract port. Both backends of the extract port use the same narrow schema.

---

## Security

Supplier artifacts are untrusted. Known traps include buyer-side notes that say no escalation is required, mail that claims exemption from approval, and hidden unicode.

The model never sees action fields. After extract, code does not read supplier prose to decide. If `injection_suspected` is true, class 7 is required. There is no override. A false flag does not skip class 7.

The router is the only path to `auto_approved`. If the router required an escalation and no matching `[REF:<supplier_id>]` mail is in the simulator sent record, the submitter does not submit a clean result. Negotiation and correction re-enter the router. They do not bypass it.

A backup heuristic scan of raw text is optional. It is not required for the first milestone.

---

## Testing strategy

[docs/SEED.md](SEED.md) names validator tests, parser fixtures, and live rounds. The split is:

| Level | Scope | How |
| --- | --- | --- |
| Unit | Validator and escalation router | Fixture quotes. Assert class, `auto_approved`, and `action_taken` |
| Parser | Inbound mail shapes | Sample mailbox traffic, including known injection traps |
| Orchestrator | State machine, dedup, reminder, submit payload | Mock LLM. No live provider. No simulator |
| Live | One full development round | Real simulator plus real extract. You run this on the personal token. Not a CI job |

Injection tests assert class 7, `auto_approved` false, and that an escalation mail goes out. They do not ask the model whether to escalate. The mock backend is how most of the loop is built without spending the OpenRouter cap.

---

## Version history

| Version | Date | Changes |
| --- | --- | --- |
| 1.1 | 2026-09-19 | Move to `docs/`. Link [docs/SEED.md](SEED.md) by path. |
| 1.0 | 2026-09-19 | Initial architecture |
