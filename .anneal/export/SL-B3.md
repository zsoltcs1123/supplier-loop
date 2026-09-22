# SL-B3 — Recomputed line total can be a binary float

**Status:** done

**Path:** SL

## Description

submit_results can send a line total that is not the cent value. 200 times 1.16 became 231.99999999999997.

## Severity

low

## Repro notes

- Development round 4, p04 rubber gasket, quantity 200 at 1.16. Payload total was 231.99999999999997.

## Notes

- Recomputed line and grand totals quantize to cents before submit.
