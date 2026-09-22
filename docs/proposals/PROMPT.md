# Proposal prompt

After a finished development round, dump a pack from the files already on disk, then write one proposal by hand. The quoting loop never runs this pass.

```bash
uv run python -m supplier_loop pack-propose
```

Do not run this during the exam. Do not call it from `run-dev`, `resume-dev`, or a poll pass. Do not auto-apply. The extract key is not used.

## Pack

Reads `.artifacts/round/round.json`, `.artifacts/ops.jsonl`, and `.artifacts/llm-spend.json`.

Writes `.artifacts/proposals/<round_id>/pack.md`.

No MCP call. No OpenRouter call.

## Allow-list

A proposal may touch:

- reminder
- quiet margin
- settle wait
- negotiation wait
- SOP wording
- Never list

Out of scope: escalation classes, `start_exam`.

## Schema

Write `docs/proposals/<round_id>.md` with this header and the proposed change:

```
status: pending
```

`status` is `pending`, `accepted`, or `rejected`.

Copy accepted clock numbers into [docs/LOOP_CONTRACT.md](../LOOP_CONTRACT.md) and `src/supplier_loop/machine/constants.py` by hand. There is no apply command.
