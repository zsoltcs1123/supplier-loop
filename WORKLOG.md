# Worklog

## Summary

My approach was to write a boring python loop with minimal LLM involvement. This achieves consistency and reliable behavior, while keeping the token costs low.

Details: [SEED](docs/SEED.md) and [ARCHITECTURE](docs/ARCHITECTURE.md).

Measured live-round numbers: [SELF-EVALUATION.md](SELF-EVALUATION.md).

## Tools

- Cursor as coding agent
- Agent Skills from my [collection](https://github.com/zsoltcs1123/ai-dev-zs): `project-seed`, `system-architecture`, `architecture`, `program-design`, `code-review`
- My [python-uv-template](https://github.com/zsoltcs1123/python-uv-template) repo
- [Anneal](.anneal/export/index.md), my private product state database (export provided)

## Process

- Phase 1: Gathering information, understanding requirements, generating project Seed (2 hours)
- Phase 2: Initialize repo from template, create Architecture.md, anneal init (2 hours)
- Phase 3: iterative development with Cursor agent based on anneal changes (6-8 hours)
  - C1: watch closely, run code review (to ensure good foundations)
  - C2-C5: one go, Cursor orchestrates, review after
  - C6-C9: babysit, improve + test
  - C10: bonus
- Phase 4: Wrap up, anneal export, session logs, assemble email etc (1-2 hours)
  - Cursor transcripts exported to [docs/cursor-sessions/INDEX.md](docs/cursor-sessions/INDEX.md)

Total: 12-14 hours.

## Ideas not implemented

- Always try crude extractor first, fallback to LLM on fail
- If image/extraction fails, retry with different/stronger model
- Proper System evolvement (primitives started in C10)
- Typer CLI

## Notes

- Server clock being so slow makes proper testing harder, and increased dev time by sitting on the loop watching nothing happening.
