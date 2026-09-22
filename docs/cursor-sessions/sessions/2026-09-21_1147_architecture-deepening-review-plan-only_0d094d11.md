# Architecture deepening review (plan only)

- **Started:** Monday, Sep 21, 2026, 11:24 AM (UTC+2)
- **Session ID:** `0d094d11-1646-4aef-80cb-53211bf63d60`
- **Project:** `supplier-loop`
- **User turns:** 4
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/0d094d11-1646-4aef-80cb-53211bf63d60/0d094d11-1646-4aef-80cb-53211bf63d60.jsonl`
- **Opening prompt:** /improve-codebase-architecture @docs/ARCHITECTURE.md no code yet, just plan

---

## User 1

/improve-codebase-architecture @docs/ARCHITECTURE.md no code yet, just plan

## Assistant

Architecture review, plan only. First I load the design vocabulary and project docs, then hunt hot spots.
[tool: Read]
[tool: Read]
[tool: Glob]
[tool: Glob]
[tool: Glob]
[tool: Glob]
[tool: GetDynamicTools]

## Assistant

[tool: Glob]
[tool: Glob]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Load design vocabulary, then scan planned architecture and repo state.
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Glob]
[tool: GetDynamicTools]

## Assistant

[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Glob]
[tool: CallDynamicTool]
[tool: CallDynamicTool]
[tool: Shell]

## Assistant

[tool: Task]
[tool: CallDynamicTool]
[tool: GetDynamicTools]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: Task]
[tool: CallDynamicTool]
[tool: CallDynamicTool]
[tool: Read]
[tool: Read]

## Assistant

Exploration done. Writing HTML report of planned deepenings, then open it.
[tool: Shell]

## Assistant

[tool: Write]

## Assistant

[tool: Shell]

## Assistant

Report at `/tmp/architecture-review-20260921-1124.html`. Plan only. Seven planned modules, no implementation.

Nine-step pass sits badly on those seven. Quote identity, classing, and `action_taken` / `auto_approved` leak across pipeline, router, store, submitter.

**Strong**
1. As-sent Quote record. Pipeline, store, submitter each can overwrite as-sent vs recomputed vs negotiated figure.
2. Split classer from supplier machine. Glued module is shallow: interface ≈ whole loop.
3. Evidence-derived submit fields. Persist facts. Derive flags from sent record. Give simulator seam a second adapter (in-memory). One MCP adapter today = hypothetical seam.
4. Correction vs negotiation as two machine paths. FAQ 15/16. Negotiation mail with no table must not overwrite line items.

**Worth exploring**
5. State vs log as two store modules. Wipe must not take audit trail.
6. Inbound mail kind classifier. Only `quote` hits extract port.

**Speculative**
7. Clock policy stays on the machine. Do not add a ClockPolicy module.

Locked, not reopened: extract is only model step; round wipe; extract port already has two adapters.

**Top:** Quote record first. Later modules all read a quote. Classer split next, same day.

Which of these would you like to explore?

## User 2

I like all of you suggestions. update the architecture doc to reflect all suggestions. then write me here what has been changed

## Assistant

Updating `docs/ARCHITECTURE.md` to lock in every accepted deepening. Reading the architecture guide and current doc first.
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: GetDynamicTools]

## Assistant

[tool: CallDynamicTool]
[tool: Read]

## Assistant

Rewriting `docs/ARCHITECTURE.md` to lock in the accepted modules, seams, and data rules. No file paths, no code.
[tool: Write]

## Assistant

`docs/ARCHITECTURE.md` is now **1.2**. Plan only. No code.

**Shape.** Seven pieces become ten modules. ASCII diagram and pass table now map the nine-step pass onto those modules. Persist is continuous, not a last box.

**New or split modules**
- **Quote record.** Pipeline is the only writer. `as_sent`, recomputed totals, optional `revised_as_sent`, negotiation figure outside line items.
- **Mail kind classifier.** Only `quote` hits extract. Questions, number-only negotiation replies, duplicates, approver rulings skip the model.
- **Classer** split from **lifecycle machine.** Classer returns classes only. No `auto_approved`, no `action_taken`.
- **Round state** and **operational log** are two modules. Wipe state. Log never truncates. No shared store interface.
- **Machine** has `correct_once` and `negotiate_once`. Approver rejection picks a path by class.
- **Submitter** derives `action_taken` and `auto_approved` from facts plus the sent record. No stored `auto_approved` bit.

**Seams**
- Simulator: two adapters now. MCP at runtime, in-memory in tests. One adapter was a hypothetical seam.
- Extract: extra fields forbidden. Pydantic default ignore would drop action fields silently.
- PDF reader stays a function inside the quote pipeline. Not a port.
- Clock policy stays on the machine. No ClockPolicy module.
- Orchestrator is inbox delta **or** a machine due-alarm.

**Tests.** Classer asserts classes, not submit flags. Orchestrator tests use mock extract **and** the in-memory simulator. Old “no simulator” row is gone.

**Also added.** Alternatives considered, key decisions with tradeoffs, future trigger for the injection heuristic. Heuristic still out of first milestone.

Which module you want grilled next, if any.

## User 3

/technical-writing on @docs/ARCHITECTURE.md and also tighten prose, remove redundancies, improve clarity/readability without loosing important info

## Assistant

Applying technical-writing plus unslop to `docs/ARCHITECTURE.md`. Loading those skills and the current doc.
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Treating the file as explanation: one mode, one name per thing, say each fact once. Merging the two “why” tables and cutting restated rules.
[tool: Write]

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
[tool: StrReplace]
[tool: StrReplace]

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
[tool: StrReplace]

## Assistant

[tool: StrReplace]

## Assistant

[tool: StrReplace]

## Assistant

`docs/ARCHITECTURE.md` is **1.3**. Same design. Shorter file.

Mode is explanation. Headings now carry the point (`The model never acts`, `Where data lives`, `Why the design looks like this`). Alternatives table and key-decisions table are one why table. Each rule lives in one home. Later sections point back instead of restating.

One name per module: extract port, classer, the machine, round state, operational log. Mail kind `quote` is not the Quote record.

Commands in an explanation file are now facts (`Tests assert…`). Fragments expanded. `only` sits next to the word it changes.

Unslop add, rule 26. Do not edit the skill from here:

```diff
- Substrate, wedge, vector, locus, vantage, nexus, primitive (as noun), harness (as metaphor), surface (as in "API surface"), bedrock, scaffolding (as metaphor), modality, paradigm, gold-plating, ratchet (as metaphor), evacuate (for moving code), endgame, north star, flywheel.
+ Substrate, wedge, vector, locus, vantage, nexus, primitive (as noun), harness (as metaphor), surface (as in "API surface"), bedrock, scaffolding (as metaphor), modality, paradigm, gold-plating, ratchet (as metaphor), evacuate (for moving code), endgame, north star, flywheel, theatre (for a step that does no work), sneak in (for extra fields), blob (for a combined path), due-ness (for whether an alarm is due), dragging in (for constructing extra modules).
```

Replacements used in the doc: "the verify step then does no work", "appear", "one follow-up path", "due checks", "constructing".

## User 4

Why the design looks like this doesnt seem too valuable. its backward looking. doc should be forward looking and light on decision explanation. high signal to noise ratio.

## Assistant

Cutting the backward-looking why section. Architecture file should state the shape, not the debate.
[tool: Read]
[tool: Read]

## Assistant

Dropping the why table. Keeping constraints an implementer needs. Cutting debate.
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

Gone. **1.4.**

Cut the whole why table. Stack table is now technology only, no rationale column. Dropped the scoring-and-exam-hours sentence, the “one adapter is not a real seam” lecture, and the “until a second reader exists” hedge.

What remains is the shape: modules, data, stack, run, tests, and what can still change. Version history still has the old debate if someone needs it.
