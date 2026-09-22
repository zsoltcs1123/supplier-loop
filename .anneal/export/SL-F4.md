# SL-F4 — Persist outbound sent log across resume

**Status:** done

**Path:** SL

## Body

McpSimulator.list_sent is process-local. After resume, submitter cannot see escalation mail, so action_taken can be reminded when the server has class-1 outbound.
