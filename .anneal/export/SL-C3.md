# SL-C3 — Classer

**Status:** done

**Path:** SL

## Kind

new_feature

## Goal

Given a Quote record, `**RFQ**` context, price history, injection_suspected, and own quote history, code returns the set of required escalation classes. The classer does not write auto_approved or action_taken.

## Deliverables

- Pure classer for rules 1 through 7. Class 7 follows injection_suspected with no override
- Unit tests assert classes only

## Notes

- Sending mail, phases, and submit flags are out of scope
- A false injection_suspected does not skip class 7

## Sequence

3

## Dependencies

- SL-C2: Mail kind classifier and fixture quote pipeline

## Required by

- SL-C4: Mock happy-path round
