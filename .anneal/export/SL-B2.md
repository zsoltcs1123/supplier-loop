# SL-B2 — Approver Not approving counts as approval

**Status:** done

**Path:** SL

## Description

A ruling that says Not approving that is stored as approval. Correction never runs. submit_results can set auto_approved true after a rejection.

## Severity

high

## Repro notes

- Round 3 Declan class 2. Body: Yes, the quantity is off versus what we requested. Not approving that — have them requote at the right quantity. Parser matches word-prefix approv, not reject. correct_once did not fire. Submitted auto_approved true.

## Notes

- Not approving is a rejection. Correction runs. auto_approved stays false.
