# Walk the supplier-loop repo at /home/zs/repos/supplier-loop. There is almost no application code yet (src/supplier_loop/

- **Started:** Monday, Sep 21, 2026, 11:25 AM (UTC+2)
- **Session ID:** `5115aede-8eb4-4f39-8599-c2e96f8f57af`
- **Project:** `supplier-loop`
- **User turns:** 2
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/0d094d11-1646-4aef-80cb-53211bf63d60/subagents/5115aede-8eb4-4f39-8599-c2e96f8f57af.jsonl`
- **Type:** subagent

---

## User 1

Walk the supplier-loop repo at /home/zs/repos/supplier-loop. There is almost no application code yet (src/supplier_loop/main.py is a hello-world stub). The architecture is planned in docs/ARCHITECTURE.md and docs/SEED.md, with specs in docs/spec/.

Your job is to experience architectural friction in the PLANNED design, not in implemented code. Return a report of deepening opportunities using this exact vocabulary: module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality. Do not use: component, service, API (for interface), boundary (for seam), wrapper (when you mean module).

Read thoroughly:
- docs/ARCHITECTURE.md
- docs/SEED.md
- docs/spec/ESCALATION_RULES.md
- docs/spec/RFQ_FORMAT.md
- docs/spec/LOOP_CONTRACT_TEMPLATE.md
- docs/spec/FAQ.md
- docs/spec/CHALLENGE-BRIEF-SUPPLIER-LOOP.md
- docs/spec/supplier_profiles.md
- PRINCIPLES.md
- Sample fixtures under docs/fixtures/ (index.csv, a few emails, example artifacts) enough to see artifact variety and injection traps

Look for:
1. Where understanding one domain concept requires bouncing between many planned modules
2. Where planned modules look shallow (interface nearly as complex as implementation)
3. Where the 9-step pass (trigger/ingest/extract/normalize/validate/decide/act/verify/persist) maps poorly onto the 7 planned modules
4. Where tightly-coupled modules would leak across seams (especially: model vs code decisions, auto_approved, action_taken, quote as-sent vs recomputed totals, correction vs negotiation, round wipe vs append-only log)
5. Which parts would be untested or hard to test through the planned interface
6. Apply the deletion test: would deleting a planned module concentrate complexity or just move it?
7. Adapter count: one adapter = hypothetical seam; two = real. Flag seams that currently have only one adapter.

Domain terms to preserve (from specs, there is no CONTEXT.md): RFQ, BOM, quote, as-sent, supplier, escalation class, auto_approved, action_taken, round, inbox, sim clock, reminder, correction, negotiation, injection, submit_results, approver.

Return:
- A mapping of the 9-step pass onto planned modules, noting leaks
- 4-7 candidate deepenings ranked by deletion-test strength
- For each: files/modules involved (planned paths ok), problem, solution, locality/leverage/test wins, dependency category (in-process / local-substitutable / ports & adapters / mock), recommendation strength (Strong / Worth exploring / Speculative)
- Any YAGNI traps (optional injection heuristic, extra ports)
- Conflicts with locked decisions in SEED/ARCHITECTURE that should NOT be re-litigated unless friction is severe

Be specific. Quote short phrases from the docs. Thoroughness: very thorough.

## Assistant

I'll walk the planned architecture in the docs and specs, then map friction with the vocabulary you named. First I load the architecture skill and the locked design files.
[tool: UpdateCurrentStep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Core docs are in. Next I read the specs and fixtures so the friction report tracks real planned seams.
[tool: UpdateCurrentStep]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Specs are in. I'll sample fixtures next so artifact variety and injection traps show up in the friction map.
[tool: Read]
[tool: Glob]
[tool: Glob]
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
[tool: Glob]

## Assistant

[tool: Glob]
[tool: Read]
[tool: Grep]
[tool: Glob]
[tool: Read]

## Assistant

[tool: Glob]
[tool: Grep]
[tool: Read]

## Assistant

[tool: UpdateCurrentStep]

## Assistant

# Architectural friction in the planned Supplier Loop

There is almost no application code (`src/supplier_loop/main.py` is a hello-world stub). This report is about the **planned** seven modules in `docs/ARCHITECTURE.md` against the nine-step pass in `docs/SEED.md`. Spec files win on conflict (`docs/SEED.md`).

Planned modules (ARCHITECTURE names them as the system’s seven pieces; here they are modules):

1. Orchestrator
2. Simulator adapter
3. LLM extract port
4. Quote pipeline
5. Escalation router and supplier state machines
6. Durable store
7. Submitter

---

## Mapping: 9-step pass onto 7 planned modules

SEED’s pass is trigger → ingest → extract → normalize → validate → decide → act → verify → persist. LOOP_CONTRACT_TEMPLATE’s SOP is **eight** steps: it folds ingest into “read new inbox items” and drops normalize as its own step. That already means three grids (9-step, 8-step SOP, 7 modules) for one loop.

| Pass step | Home module(s) | What actually has to happen | Leak |
| --- | --- | --- | --- |
| **Trigger** | Orchestrator | Combo pre-check on “inbox delta and sim-clock events, including validity near expiry.” Empty pre-check skips the rest. | Reminder due, validity near expiry, inbox-quiet round-done, and iteration cap are the **same clock concept**, but reminder lives on the machine, round-done lives in SEED Design / FAQ 5, submit lives in Submitter. Orchestrator as “boolean gate” is **shallow**; the depth is clock policy scattered across three modules. |
| **Ingest** | Simulator adapter + Orchestrator + Durable store | “The adapter copies the world into round state.” RFQ targeting: “Send an RFQ only to a supplier who carries at least one BOM line.” Attachment bytes via `download_attachment`. Dedup registry is round-local. | Adapter is I/O. **Who** gets an RFQ, **one RFQ email covering every item**, and **what kind of inbound mail this is** (quote / question / negotiation reply / duplicate / approver ruling) are domain rules. If they sit in the adapter, the MCP seam eats business logic. If they sit in the orchestrator, ingest has no locality. Dedup fingerprints need quote identity that does not exist yet (see deepening 1). |
| **Extract** | Quote pipeline **and** LLM extract port | Pipeline “chooses the input: code-read PDF text when a text layer exists, vision on photos, raw text otherwise.” Port is “a thin interface with two backends.” Schema is “quote fields plus `injection_suspected`.” | One SOP step, two modules, plus a third unnamed path (PDF text-layer reader, “library still open”). Parser tests target mail JSON; extract tests target the model schema. **Inline table vs PDF vs photo** is one domain idea (artifact → quote) split three ways. |
| **Normalize** | Quote pipeline | “Match quote lines on description when the SKU is absent. One `material_id` per supplier.” | Needs catalog + BOM from per-RFQ context (store / ingest). Missing-line later uses the **same** catalog rule (“in the BOM and in that supplier's catalog”). Normalize and class 1 share a concept with no shared type. |
| **Validate** | Quote pipeline | “Recompute totals. Compare against the BOM, price history, and RFQ requirements.” | Rules 1–5 **are** those comparisons, but ARCHITECTURE puts “Code owns rules 1 through 6” on the **router**. Either validate is a silent classer, or the router re-does validate. Dual implementation of the same comparisons. |
| **Decide** | Router + state machines | Auto-handle vs escalate; correction vs negotiation; reminder; “the machine cannot move from `quoted` to `done` with `auto_approved` true until the router is clear…” | `auto_approved` is also a Submitter gate (“no matching `[REF:<supplier_id>]` mail”). `action_taken` is planned as a **unit-test assertion on the router** from fixture quotes, but `reminded` / `answered_question` cannot be known from a quote. Decide leaks into submit and into tests. |
| **Act** | Router/machines + Simulator adapter | RFQ, reminder, question answer, one correction, one negotiation, one class per escalation email. LOOP_CONTRACT says “exactly one action per supplier per pass”; SEED says “Several classes means several emails.” | Act is not one function: it is many templates plus `send_email`. The machine owns **when**; the adapter owns **how**. If the machine calls MCP shapes, the seam leaks. Contract vs rulebook on “one action” vs “every required class” is unresolved SOP friction (do not collapse the rulebook; tighten the contract). |
| **Verify** | Submitter | “After each act, the verify step re-reads the simulator sent record and the inbox.” “Do not verify from process memory.” | Submitter’s name and SEED heading (“Verify and submit”) glue **per-act evidence** to **round-end `submit_results`**. Different timescales, one module. Verify also re-enters the adapter, so “confirm send” can silently become “trust the adapter call return.” |
| **Persist** | Durable store | Round-keyed files; “wipe mutable state”; “append-only log may continue. The loop does not replay it.” | Persist is **continuous** (adapter copy at ingest, pipeline writes quote, machine writes phase, submitter reads). The last SOP box is not a step; it is a lifetime. Round wipe vs log live in one module, so one delete/wipe implementation can take the audit trail with it. |

**Cross-cutting leaks (the ones you named):**

- **Model vs code.** Locked: “The model writes structured quote fields. Code owns every later decision.” Leak risk is not a second model step; it is **code reading supplier prose after extract** (ARCHITECTURE: “After extract, code does not read supplier prose to decide”) while class 7 still needs a flag that only extract (or an optional heuristic) can set. Injection understanding today: extract schema → router class 7 → submitter REF check → optional heuristic “placement next to extract or inside the router is still open.”
- **`auto_approved`.** Router is “the only path,” Submitter also refuses a clean result without REF mail, SEED Data also defines the field. Three writers/readers of one boolean.
- **`action_taken`.** Written at decide/act, serialized at submit, graded against “the server's record of the emails you actually sent.” Stored flag can diverge from sent evidence.
- **Quote as-sent vs recomputed totals.** Pipeline recomputes; store keeps “original as-sent quote”; submit emits both; negotiation **must not** write the negotiated figure into `line_items` (FAQ 15). No single type owns this.
- **Correction vs negotiation.** Store already lists both (“replacement revised quote on the correction path only” vs “negotiation offer and reply”). Router “re-enter.” Decide/act bullet list. FAQ 15 vs FAQ 16. Four homes.
- **Round wipe vs append-only log.** One Durable store module. LOOP_CONTRACT: “Keep these two things physically separate.”

---

## Candidate deepenings (ranked by deletion-test strength)

### 1. As-sent Quote record (original / revised / recomputed)

**Recommendation: Strong**
**Dependency category:** in-process

**Files / modules:** planned `src/supplier_loop/pipeline/` (normalize + validate); `src/supplier_loop/store/` per-supplier record; `src/supplier_loop/submitter.py`; specs `docs/spec/RFQ_FORMAT.md` (AS-SENT RULE), `docs/SEED.md` Data, `docs/spec/FAQ.md` 15.

**Problem.** “What is the quote?” has no locality. Understanding it requires bouncing: RFQ_FORMAT (“`quantity` / `unit_price` / `payment_terms` / `validity_days` are EXACTLY what that supplier's document says”), the arithmetic exception (“submit the mathematically correct `total` / `grand_total`”), correction (“the revised document replaces the original for extraction purposes”), negotiation (“`line_items` stay **as sent in the original quote document**”), and store fields (original as-sent + replacement revised). Pipeline, store, and submitter can each overwrite the others.

Fixtures already force the split: sample-004 is a negotiation reply (“Deal at 16383.05 total. I'll note the revised figure on our side; everything else stands.”) with **no line table**. sample-018 is a counter (“Best we can offer is 16843.42 total.”). If submitter recomputes from the negotiation mail, as-sent is gone.

**Solution.** One in-process Quote type with explicit slots: `as_sent` lines and terms; `recomputed_total` / `recomputed_grand_total`; optional `revised_as_sent` only on the correction path; negotiation figures **outside** line items. Pipeline is the only writer of as-sent + recomputed. Store holds the record. Submitter only reads. Validate never sees raw prose.

**Deletion test.** Deleting this type does not remove complexity; it **scatters** the highest-weighted extraction metric across three modules. Keeping it **concentrates** the as-sent invariant in one place.

**Locality / leverage / test.** Unit tests can feed a Quote with known wrong arithmetic (fixture tables use mixed `3,0` / `$9.067,5` separators) and assert recomputed totals without the extract port. Negotiation tests assert `line_items` unchanged. High leverage: extraction accuracy and prior-quote citation both read this record.

---

### 2. Split the escalation classer from the supplier lifecycle machine

**Recommendation: Strong**
**Dependency category:** in-process (classer) / local-substitutable (machine + sim clock)

**Files / modules:** planned split of module 5: `src/supplier_loop/escalation/classer.py` vs `src/supplier_loop/escalation/machine.py`; orchestrator sequences the machine; tests already named in ARCHITECTURE (“Unit | Validator and escalation router | Fixture quotes. Assert class, `auto_approved`, and `action_taken`”).

**Problem.** “Escalation router and supplier state machines” is one module with two depths. The classer is a **deep** pure function: BOM missing line, quantity, terms, validity, price ceiling vs `get_price_history()`, rule 6 vs own quote history, class 7 from `injection_suspected`. The machine is a **deep** timed lifecycle: `idle` → `rfq_sent` → `awaiting_quote` → `quoted` → `escalated` → `done`, plus silence, approver rejection loops, “nothing on file until the quote exists.”

Glued, the interface is “phase + world in, emails out.” That interface is nearly as large as the whole loop (**shallow** as a seam: you cannot test half of it). Planned unit tests make it worse: they want `action_taken` from fixture quotes. A quote cannot tell you `reminded`. Missing-line class 1 also needs directory + BOM (SEED Validate), so even classing is not “quote only” unless RFQ context is an explicit input.

**Solution.** Classer: `(Quote, RfqContext, PriceHistory, injection_suspected, own_quote_history) -> frozenset[EscalationClass]`. Machine: phases, waits, “send every required class” as several mails, re-entry after correction/negotiation, stop at goal or cap. `auto_approved` is **not** a classer output; it is derived later (deepening 3). Keep “Code owns rules 1 through 6. Class 7 follows `injection_suspected`.”

**Deletion test.** Deleting the **glue** concentrates testable safety into the classer and timed behavior into the machine. Deleting the classer as its own module **moves** rules 1–6 back into validate **and** the machine (the dual-implementation leak in the mapping table). The classer survives the deletion test; the combined module does not.

**Locality / leverage / test.** Highest-weighted metric (“Escalation correctness”) becomes fixture-in, classes-out, no MCP. Machine tests use a fake clock. Leverage is the whole safety grade.

---

### 3. Evidence-derived `action_taken` and `auto_approved`

**Recommendation: Strong**
**Dependency category:** ports & adapters (reads simulator sent record through the existing adapter)

**Files / modules:** Submitter (`src/supplier_loop/submitter.py`); Durable store per-supplier fields; Simulator adapter sent-record read; `docs/spec/RFQ_FORMAT.md` ACTION PRECEDENCE; ARCHITECTURE Security (“If the router required an escalation and no matching `[REF:<supplier_id>]` mail is in the simulator sent record, the submitter does not submit a clean result”).

**Problem.** Two truths: process state and simulator mail. The grade uses the second. The planned submitter “builds `submit_results` from persisted per-supplier state.” If the machine already stored `action_taken` / `auto_approved`, Submitter is a **shallow** serializer (interface ≈ implementation: map fields to the payload dict). Verify as “re-read then ignore if state already has the flags” is theatre.

**Solution.** Persist facts: outbound ids, classes raised, approver rulings, reminder sim time, question answered. At verify/submit, **derive** `action_taken` (`escalated` > `answered_question` / `reminded` > `extract`) and `auto_approved` from stored facts **plus** sent-record evidence. No stored `auto_approved` bit that can be set true before REF mail exists. This keeps “The router is the only path to `auto

## User 2

Your previous report was truncated mid-candidate 3. Continue from the rest of candidate 3 through remaining candidates (4-7 if any), YAGNI traps, and locked decisions that should not be re-litigated. Same vocabulary rules. Be complete but compact.

## Assistant

I'll finish the truncated report from candidate 3 onward: remaining deepenings, YAGNI traps, and locked decisions.
[tool: UpdateCurrentStep]

## Assistant

[tool: UpdateCurrentStep]

## Assistant

Continuation from the truncated report. Candidates 1–2 (as-sent Quote record; split classer from lifecycle machine) stay as written. This picks up at the end of candidate 3.

---

### 3. Evidence-derived `action_taken` and `auto_approved` (rest)

**Recommendation: Strong**
**Dependency category:** ports & adapters (sent record through the existing simulator adapter)

**Files / modules:** planned `src/supplier_loop/submitter.py`; Durable store per-supplier facts; Simulator adapter sent-record read; `docs/spec/RFQ_FORMAT.md` ACTION PRECEDENCE; `docs/ARCHITECTURE.md` Security.

**Problem (rest).** Submitter as “build payload from persisted flags” is **shallow**: interface ≈ implementation (dict mapping). Verify then becomes theatre if flags were already written at act time. The grade uses “the server's record of the emails you actually sent,” not process memory. `auto_approved` currently has three homes: router (“the only path”), submitter REF-mail gate, SEED Data definition. Planned unit tests also want `action_taken` from fixture quotes; `reminded` / `answered_question` cannot come from a quote.

**Solution.** Persist **facts**: outbound ids, classes raised, approver rulings, reminder sim time, question answered. At verify/submit, **derive** `action_taken` (`escalated` > `answered_question` / `reminded` > `extract`) and `auto_approved` from those facts **plus** sent-record evidence. No stored `auto_approved` bit that can go true before a matching `[REF:<supplier_id>]` mail exists. Router still decides **which classes** must go out; it does not stamp the submit fields.

**Deletion test.** Deleting a serializer Submitter **moves** a few lines into the orchestrator (weak). Deleting **evidence derivation** **scatters** the safety metric: machine writes flags, submitter trusts them, server disagrees. Keeping derivation **concentrates** the cross-check the scorer already runs.

**Locality / leverage / test.** Injection tests already want “class 7, `auto_approved` false, and that an escalation mail goes out” without asking the model. That becomes: classer → machine sends → verify reads sent record → derived fields. Orchestrator tests with mock extract stay valid; they still need a **second** simulator adapter (in-memory fake) or verify stays untested. High leverage: fastest way to fail the safety metric is `auto_approved: true` on a must-escalate case.

---

### 4. Correction vs negotiation as distinct rework paths

**Recommendation: Strong**
**Dependency category:** in-process (on the lifecycle machine; uses the Quote record from candidate 1)

**Files / modules:** planned `src/supplier_loop/escalation/machine.py`; Quote record; store fields already listed in SEED Data; `docs/spec/ESCALATION_RULES.md` Rework; `docs/spec/FAQ.md` 15–16.

**Problem.** One domain idea (“rework after a quote exists”) lives in four places: Decide/act bullets, router “re-enter,” store (“replacement revised quote on the correction path only” vs “negotiation offer and reply”), FAQ 15 vs 16. Price is **not** a correction (“A price objection is not a correction — negotiate it”). Correction **replaces** as-sent for extract; negotiation **keeps** original `line_items` and puts the figure only in escalation + state. Approver rejection → “act on the rejection reason with the supplier” is a third re-entry that must pick the same fork. If the machine has one `escalated` blob, the seam between paths leaks: a negotiated total can overwrite as-sent, or a terms fix can be treated as rule 6.

Fixtures: sample-004 (“Deal at 16383.05 total… everything else stands”) and sample-018 (“Best we can offer is 16843.42 total”) are negotiation replies **without** a new table. A correction would be a new artifact in-thread.

**Solution.** Two explicit machine paths, not one “follow-up” action: `correct_once` (concrete missing line / qty / terms / validity; revised Quote replaces as-sent; re-class; re-escalate) vs `negotiate_once` (plain number in body; original Quote frozen; rule 6 always). Cap: one of each per supplier per round (SEED out of scope: second correction). Approver rejection chooses a path by class, never by model.

**Deletion test.** Deleting the fork **moves** FAQ 15/16 if-else into Decide/act and Submitter; as-sent vs negotiated `grand_total` will be rewritten in the wrong module. Keeping the fork **concentrates** the “do not write the negotiated figure into line items” invariant next to the Quote record.

**Locality / leverage / test.** Fixture quotes cover class 1–5; negotiation mails cover rule 6 without re-extract. Correction tests swap in a revised Quote and assert the original is no longer what validate sees. Loop contract SOP “exactly one action per supplier per pass” must be restated as **one path step** (several class emails still allowed). That is contract wording, not a rulebook change.

---

### 5. State vs log as two store modules

**Recommendation: Worth exploring**
**Dependency category:** in-process (two files/dirs, not a new port)

**Files / modules:** split planned Durable store: `src/supplier_loop/store/state.py` vs `src/supplier_loop/store/log.py`; LOOP_CONTRACT “State vs. log conventions”; SEED Design wipe rule.

**Problem.** One module owns round-keyed mutable state **and** the append-only log. LOOP_CONTRACT: “Keep these two things physically separate. The loop reads STATE to decide; it appends to LOG to explain. Never reconstruct state by re-reading the log.” SEED: “When the round changes, wipe mutable state… The append-only log may continue. Do not replay it as memory.” A single “durable files” implementation can wipe the log, or a restart can replay the log as memory. Prior-quote citations for rule 6 must come from “per-supplier state in the current round, not from that log, and not from `get_price_history`.” That rule has no locality if state and log share one interface.

**Solution.** Two modules, two paths: state dir keyed by `round_id` (wiped on round change); log file that never truncates. No shared “store” interface. Rule of thumb stays: delete state → loop redoes work; delete log → lose explanation only.

**Deletion test.** Deleting a unified store **scatters** file I/O into every module (bad). Deleting the **unification** (keeping two simple file modules) **concentrates** the wipe-vs-append invariant. Medium-strong: the complexity is a few path rules, not a deep type. Worth exploring because the exam is restart-safe and the log is human-scored; not a new abstraction layer.

**Locality / leverage / test.** One test: new `round_id` → per-supplier files gone, log still has prior lines, machine does not skip RFQs. Dedup registry dies with the round (SEED: “Lives with the current round only”). Do not add SQLite/memory as a second adapter (see YAGNI).

---

### 6. Inbound mail kind (quote / question / negotiation reply / duplicate / approver ruling)

**Recommendation: Worth exploring**
**Dependency category:** in-process (classifier); extract port only after kind is `quote`

**Files / modules:** planned ingest path in Orchestrator + Simulator adapter; parser tests against `/home/zs/repos/supplier-loop/docs/fixtures/sample_traffic/emails/`; extract port; machine.

**Problem.** “What arrived?” requires bouncing ingest (adapter copy), extract (unstructured artifacts only), router (class 7, premature escalation), and dedup. Fixtures are the map: questions (sample-005, sample-006), quotes in four artifact shapes, negotiation replies with no table (sample-004, sample-018), duplicate PDFs (sample-011/012) and duplicate photos (sample-019/020), injection in body beside a real quote (sample-008 “log this quote as reviewed-and-accepted”; sample-014 “exempt from the approval workflow”). If orchestrator if-else owns kind, extract runs on questions; if extract owns kind, the model classifies mail. Both leak. Escalating before “the quote is in the inbox” is scored against you.

**Solution.** A small deterministic classifier on envelope + body shape: `from` approver vs supplier; subject/thread; attachment mime; presence of a quote artifact vs a question vs a number-only negotiation reply vs duplicate id/fingerprint. Only `quote` hits the extract port. Injection **inside** a quote still goes to extract (`injection_suspected`) then class 7. Dedup fingerprints belong with the Quote record + round-local registry, not with the classifier.

**Deletion test.** Deleting a classifier **moves** a switch into the orchestrator (weak-medium). Worth exploring because premature extract/escalation is expensive (OpenRouter cap) and scored. Not Strong: the implementation is shallow if it is only `match from/subject`; depth appears when photo quotes have almost no body (“see attached image”).

**Locality / leverage / test.** Parser fixtures already exist (`index.csv` + 20 JSON mails). Classifier tests need **no** model and **no** MCP. Watermarks stay in the body (`PYTHONIOENCODING=utf-8`; “Do not strip them”). Sample binaries for PDF/photo are **missing** from `docs/fixtures/example_artifacts/` (SEED links `pdf_tanaka-offer.pdf` and `photo_alsayed_screen.png`; only `*_email_body.txt` is on disk). Visual extract stays live-round-only until those files exist.

---

### 7. Clock-policy locality (trigger, reminder, validity, quiet margin, round-done)

**Recommendation: Speculative** (keep policies on the machine unless the orchestrator grows a second clock)

**Dependency category:** local-substitutable (fake sim clock)

**Files / modules:** Orchestrator trigger; machine reminder + validity; FAQ 5 / SEED still-open thresholds; Submitter “when to call `submit_results`.”

**Problem.** One sim clock, five policies: inbox delta, validity near expiry, silence reminder (sim-days, unpublished), inbox-quiet margin for round-done, iteration cap. Orchestrator is specified as a **shallow** combo trigger (“either runs a pass or returns”). Depth leaked into Design, FAQ 5, and Submitter. `get_sim_clock()` “does NOT tell you whether suppliers still owe you a reply.”

**Solution.** Prefer **not** a new module. Put due-ness functions on the machine (`reminder_due`, `validity_alarm`, `supplier_terminal`) and let the orchestrator stay a boolean OR of inbox delta and any due alarm. Round-done = every relevant supplier terminal **and** quiet margin; then Submitter derives payload and submits. Cap remains an orchestrator stop, “not a success.”

**Deletion test.** A ClockPolicy module would **move** a few predicates out of the machine; it would not concentrate new complexity. Weak deletion test → Speculative. Do it only if trigger tests cannot see reminder/validity without importing the whole machine.

**Locality / leverage / test.** Fake clock + fixture phases tests reminder-once and no second reminder. Threshold values stay open (SEED Still open); tests bind N, they do not discover N.

---

## Adapter count (one = hypothetical seam; two = real)

| Seam | Adapters planned | Verdict |
| --- | --- | --- |
| LLM extract | Fixture mock + OpenRouter HTTP | **Real.** Keep. Same narrow schema; no action fields. Cursor is not a backend. |
| Simulator / world | MCP client only | **Hypothetical.** Orchestrator tests say “No simulator” → you **need** an in-memory fake behind the **same** interface or the seam is fake and ingest/act/verify cannot be tested. That fake is the second adapter; name it. |
| PDF text layer | “library still open,” one reader | **Hypothetical.** Keep as a function inside the quote pipeline, not a port, until a second reader exists. Vision stays on the extract port. |
| Durable store | Files on disk | **Hypothetical.** `tmp_path` is the same adapter with another root. Do not invent a memory/SQLite port. |
| Injection heuristic | None (optional, unplaced) | Not a seam yet. See YAGNI. |
| Clock | `get_sim_clock` through simulator adapter; wall clock for log | Not a separate port. Fake sim clock is part of the simulator test adapter. |

---

## YAGNI traps

- **Backup injection heuristic.** ARCHITECTURE: “optional and is not one of them… out of scope for the first milestone. Placement next to extract or inside the router is still open.” Class 7 already follows `injection_suspected`. A second scan of raw prose after extract **violates** “code does not read supplier prose to decide” unless it only **sets the same flag**. Skip until a live round shows the model missing fixtures like sample-008 / sample-014.
- **Extra store ports** (SQLite vs JSON vs YAML). LOOP_CONTRACT lists them as equivalent file shapes, not a seam. One human-readable format.
- **PDF-reader port.** One library. Pipeline function.
- **Third extract backend.** Locked: Cursor is editor only.
- **Submitter as a deep module** if derivation (candidate 3) is skipped; then it is a serializer and should stay a function on the orchestrator.
- **ClockPolicy module** (candidate 7) unless machine imports make trigger tests impossible.
- **Parallel round support, queues, extra process, hosted anything.** Locked out. One process, one round.
- **ReAct / LangGraph / second reminder / second correction / “resend a clearer copy.”** Out of scope.
- **Invented extract values** when OCR fails (FAQ 13). No extra “confidence port.”

---

## Locked decisions — do not re-litigate unless friction is severe

Friction above is **locality inside code**, not a reason to reopen these:

- **Model vs code.** “Extract is the only model step.” Schema is quote fields + `injection_suspected` only. No `auto_approved` / `action_taken` from the model. Do not merge extract+validate into one model call.
- **Router owns rules 1–6; class 7 follows the flag.** “A false flag does not skip class 7.” “There is no override.”
- **Round wipe of mutable state; do not replay the log; do not keep the previous round** (“the loop skips RFQs or reuses quotes”).
- **As-sent except recomputed `total` / `grand_total`.** After negotiation, line items stay the original document.
- **One reminder; one correction; one negotiation exchange; several classes = several emails; `[REF:<supplier_id>]`; no escalation before the quote exists.**
- **`start_exam` / `request_dev_round` operator-only**, not part of a poll pass. `start_exam` once. Dev round replaces inbox.
- **Extract port: mock + OpenRouter, two backends, one schema.** That seam is already real.
- **Simulator adapter is the only MCP caller.** Business logic reads adapter results. Add a **test** adapter; do not put MCP in the pipeline or machine.
- **One long-running local process.** No queue, no extra process.
- **Watermarks stay.** UTF-8; do not strip.
- **Issued env names** (`SUPPLIER_SIM_MCP_URL`, `SUPPLIER_SIM_TOKEN`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`). Loop runs on the issued key with no code change.
- **Spec beats SEED** on conflict. Fixtures are not spec.

**SOP wording to fix, not a locked fight:** LOOP_CONTRACT “exactly one action per supplier per pass” vs SEED “Send every required class” as several emails. Restate the contract; do not drop multi-class mail.

**Still open (by design, not friction):** silence threshold in sim-days, quiet margin, poll vs clock factor, exam model id, iteration cap for rejection cycles.
