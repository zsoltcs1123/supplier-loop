# Projects

## (all) — All projects

| Code | Title | Description | Status |
| --- | --- | --- | --- |
| SL | Supplier Loop | Supplier Loop is an unattended quoting loop against the LeadFlow Automation supplier simulator. The loop reads each RFQ, emails the suppliers who can fill it, extracts quotes, validates them in code, escalates when docs/spec/ESCALATION_RULES.md requires it, and calls submit_results before the deadline.

This is a timed evaluation, not a product. Extract is the only model step. Code owns every later decision. The model never acts.

Out of scope: a ReAct agent that makes every decision; LangGraph or another heavy agent framework as the default; invented extraction values; an escalation that says the loop could not read the artifact; a second reminder or a second correction request; parallel development rounds. | live |
