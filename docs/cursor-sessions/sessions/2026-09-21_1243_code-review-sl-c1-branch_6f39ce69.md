# Code review: SL-C1 branch

- **Started:** Monday, Sep 21, 2026, 12:28 PM (UTC+2)
- **Session ID:** `6f39ce69-7aaa-4aa7-9f59-26679938ff1a`
- **Project:** `supplier-loop`
- **User turns:** 3
- **Source:** `/home/zs/.cursor/projects/home-zs-repos-supplier-loop/agent-transcripts/6f39ce69-7aaa-4aa7-9f59-26679938ff1a/6f39ce69-7aaa-4aa7-9f59-26679938ff1a.jsonl`
- **Opening prompt:** /code-review this branch vs main

---

## User 1

/code-review this branch vs main
spec: /anneal sl-c1

## Assistant

Reviewing this branch against main, grounded in anneal `sl-c1`. Loading review layers, anneal spec, and the diff.
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

Need anneal spec, branch diff vs main, and coding rules next.
[tool: Shell]
[tool: Shell]
[tool: Shell]
[tool: Glob]
[tool: Glob]
[tool: Glob]

## Assistant

[tool: Read]
[tool: Read]
[tool: Shell]
[tool: Shell]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Shell]

## Assistant

[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: GetDynamicTools]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

[tool: GetDynamicTools]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Read]

## Assistant

[tool: CallDynamicTool]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: CallDynamicTool]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Read]

## Assistant

[tool: Read]
[tool: Grep]
[tool: Shell]
[tool: Grep]

## Assistant

[tool: Read]
[tool: Grep]
[tool: Read]
[tool: Read]
[tool: Read]

## Assistant

Review: `feat/in-memory-simulator` vs `main` (21 files). Spec: C1 (in-memory simulator, round state, operational log). Interactive mode. Unstaged `.gitignore` not in branch; ignored.

## Summary

Branch adds simulator Protocol plus in-memory adapter, disk round state with snapshot/wipe, append-only JSONL log, and stdout progress printer. Pydantic models forbid extra fields. Tests hit adapter, persist, and wipe-vs-log. No live MCP.

## Findings by layer

**1 Code quality**
- Medium: `InMemorySimulator` getters hand out live internals (`memory.py:43-50`, `72-75`, `86-87`). Callers can mutate assignment, directory, history, attachments, last submit.
- No bugs found in snapshot/wipe/log write path. Set + `QuoteRecord` JSON roundtrip works (checked outside tests).

**2 Conventions**
- Medium: `SentEmail` is a plain class, not a dataclass (`memory.py:14-19`). `python.mdc` wants dataclasses for data models.
- Medium: doc conflict, not a code bug. `python.mdc` prefers dataclasses; `docs/SEED.md` already picked Pydantic. Code follows seed. Do not rewrite models.

**3 Principles**
- Minor: `snapshot_world` sits below `RoundStore` even though it calls `save` (`store.py:8-61`). Stepdown wants high-level first.

**4 Security**
- No issues. `extra="forbid"` blocks `action_taken` / `auto_approved` in round state. Secrets stay out. UTF-8 on log and state.

**5 Testing**
- Medium: `test_log_append_writes_jsonl_without_printing_stdout` never captures stdout (`test_log.py:14,55`). Unused `StringIO` stays empty. Name overclaims.
- Medium: `test_progress_emit_writes_plain_text_when_called` asserts strings never passed in (`test_progress.py:23-35`). Does not earn keep.
- Medium: store tests never persist a filled `QuoteRecord` or non-empty `DedupRegistry`. Type exists; roundtrip untested in suite.

**6 Spec (C1)**
- No gaps on stated deliverables. Nine adapter methods, round state slots, wipe leaves log, no MCP. Negotiation offer/reply from seed not on `SupplierFacts`; architecture defers that to later machine work.

## Totals

Medium 6 · Minor 1 · Major 0

---

Issue 1/6 (Medium). Highest first.

`get_assignment`, `get_supplier_directory`, `get_price_history`, `get_sim_clock`, `download_attachment`, and `submit_results` return the objects stored inside the fake. `list_inbox` and `sent_emails` copy. Later tests that mutate a returned assignment or directory will change simulator state.

```43:50:src/supplier_loop/simulator/memory.py
    def get_assignment(self) -> Assignment:
        return self._assignment

    def get_supplier_directory(self) -> list[SupplierEntry]:
        return self._directory

    def get_price_history(self) -> list[PriceHistoryRow]:
        return self._history
```

Fix: return copies. `model_copy(deep=True)` on models. `list(...)` on directory/history. Copy the attachments dict and the submit payload.

**Fix / Skip / Discuss?**

## User 2

fix

## Assistant

Copying adapter returns so callers cannot mutate simulator state. Then next issue.
[tool: GetDynamicTools]
[tool: Read]
[tool: Read]

## Assistant

[tool: CallDynamicTool]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: Read]

## Assistant

[tool: StrReplace]

## Assistant

[tool: StrReplace]
[tool: Shell]

## Assistant

[tool: Shell]

## Assistant

Getters now return deep copies. Constructor, `push_inbox`, `submit_results`, and `sent_emails` copy too. Unit test mutates every returned handle; store stays intact.

---

Issue 2/6 (Medium).

`SentEmail` is a bag of fields. `python.mdc` wants dataclasses for data models.

```14:19:src/supplier_loop/simulator/memory.py
class SentEmail:
    def __init__(self, email_id: str, to: str, subject: str, body: str) -> None:
        self.id = email_id
        self.to = to
        self.subject = subject
        self.body = body
```

Fix: `@dataclass` with `id`, `to`, `subject`, `body`. Copy via `dataclasses.replace`.

**Fix / Skip / Discuss?**

## User 3

fix this and all remaining issue as per your recommendation. commit and update PR afterwards.

## Assistant

Fix remaining review items, then commit and update the PR. Skipping the pydantic/dataclass doc conflict: code already follows seed.
[tool: GetDynamicTools]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Read]
[tool: Grep]
[tool: Shell]

## Assistant

[tool: CallDynamicTool]
[tool: Read]
[tool: Read]
[tool: Grep]

## Assistant

[tool: CallDynamicTool]
[tool: CallDynamicTool]

## Assistant

[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: StrReplace]
[tool: Write]
[tool: Write]
[tool: Write]
[tool: StrReplace]
[tool: StrReplace]

## Assistant

[tool: StrReplace]
[tool: Read]
[tool: Read]

## Assistant

[tool: Shell]

## Assistant

[tool: Shell]
[tool: Shell]
[tool: Shell]

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

Review fixes landed in `c3730f5` and pushed.

**Fixed**
- `SentEmail` is a dataclass; `sent_emails` copies with `replace`
- `python.mdc` now allows Pydantic for schemas and durable state
- `snapshot_world` sits above `RoundStore`
- Log test captures real stdout via `capsys`
- Dropped the progress test that asserted unused strings
- Store test roundtrips a filled `QuoteRecord` and non-empty dedup sets

**Skipped**
- None of the remaining review items

PR: https://github.com/zsoltcs1123/supplier-loop/pull/5
