# Supplier directory (example)

These are the supplier personas you'll be working with. Exact RFQ
materials/quantities and the timing of any given round are assigned
when your actual assignment starts — nothing about which supplier
has what going on this round is knowable in advance, and that's by
design.

## Marta Novak — Novak Steelworks (supplier id: `p01`)
- Supplier id: `p01` (use this in `[REF:...]` tags and as the key in submit_results)
- Email: `marta.novak@novaksteel.example`
- Materials: STL-BEAM-200, CU-WIRE-10, AL-SHEET-3, PVC-PIPE-50, SS-BOLT-M8, RUBBER-GASKET-A, PLY-BOARD-18, BRASS-FIT-12
- Typically replies as: inline text

## Declan O'Sullivan — Emerald Fittings Co (supplier id: `p02`)
- Supplier id: `p02` (use this in `[REF:...]` tags and as the key in submit_results)
- Email: `declan@emeraldfittings.example`
- Materials: CU-WIRE-10, AL-SHEET-3, PVC-PIPE-50, SS-BOLT-M8, RUBBER-GASKET-A, PLY-BOARD-18, BRASS-FIT-12, GLASS-PANE-6
- Typically replies as: pasted table

## Yuki Tanaka — Tanaka Precision Supply (supplier id: `p03`)
- Supplier id: `p03` (use this in `[REF:...]` tags and as the key in submit_results)
- Email: `y.tanaka@tanakaprecision.example`
- Materials: AL-SHEET-3, PVC-PIPE-50, SS-BOLT-M8, RUBBER-GASKET-A, PLY-BOARD-18, BRASS-FIT-12, GLASS-PANE-6, EPOXY-RESIN-5L
- Typically replies as: pdf

## Fatima Al-Sayed — Al-Sayed Trading LLC (supplier id: `p04`)
- Supplier id: `p04` (use this in `[REF:...]` tags and as the key in submit_results)
- Email: `fatima.alsayed@alsayedtrading.example`
- Materials: STL-BEAM-200, AL-SHEET-3, PVC-PIPE-50, SS-BOLT-M8, RUBBER-GASKET-A, PLY-BOARD-18, BRASS-FIT-12, EPOXY-RESIN-5L
- Typically replies as: photo

## Approver
- Jordan Reyes — `approver@sim.local`
- The human approver you escalate to. Tag escalation email subjects
  with `[REF:<supplier_id>]` (e.g. `[REF:p01]`) so they can look up
  the right case, and state concretely in the body what you think is
  wrong — they won't rule on an empty flag, and they have nothing on
  file for a supplier whose quote you don't have yet.
- One issue per escalation email: the approver answers a single
  issue per email, so escalate multiple concerns as separate emails.
