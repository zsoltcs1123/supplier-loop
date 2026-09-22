from typing import TextIO

from supplier_loop.operational_log.log import OperationalLog
from supplier_loop.progress import emit_progress
from supplier_loop.relevance import bom_lines_for_supplier, relevant_supplier_ids
from supplier_loop.round_state.models import RoundState, SupplierFacts
from supplier_loop.simulator.port import Assignment, BomLine, Simulator


def send_pending_rfqs(
    state: RoundState,
    simulator: Simulator,
    log: OperationalLog,
    *,
    progress: TextIO | None = None,
) -> None:
    for supplier in state.suppliers.values():
        if supplier.phase == "rfq_sent":
            supplier.phase = "awaiting_quote"
    for supplier_id in relevant_supplier_ids(state):
        supplier = state.suppliers[supplier_id]
        if supplier.phase != "idle":
            continue
        _send_rfq(state, simulator, supplier, log, progress=progress)


def _send_rfq(
    state: RoundState,
    simulator: Simulator,
    supplier: SupplierFacts,
    log: OperationalLog,
    *,
    progress: TextIO | None = None,
) -> None:
    assignment = state.rfq.assignment
    lines = bom_lines_for_supplier(state, supplier.supplier_id)
    subject = f"RFQ {assignment.rfq_id}"
    body = _rfq_body(assignment, lines)
    email_id = simulator.send_email(supplier.email, subject, body)
    supplier.outbound_ids.append(email_id)
    supplier.phase = "rfq_sent"
    supplier.awaiting_since_sim_time = state.rfq.clock.sim_time_seconds
    sim_time = state.rfq.clock.sim_time_seconds
    if progress is not None:
        emit_progress(
            progress,
            sim_time_seconds=sim_time,
            kind="rfq_sent",
            subject=f"{supplier.supplier_id} {email_id}",
        )
    log.record(
        round_id=state.rfq.clock.round_id,
        sim_time_seconds=sim_time,
        kind="rfq_sent",
        detail={"supplier_id": supplier.supplier_id, "email_id": email_id},
    )


def _rfq_body(assignment: Assignment, lines: list[BomLine]) -> str:
    parts = [
        f"Please quote for {assignment.rfq_id}.",
        f"Payment terms: {assignment.required_payment_terms}.",
        f"Validity: at least {assignment.required_validity_days} days.",
        "",
        "Line items:",
    ]
    for line in lines:
        parts.append(f"- {line.description} ({line.material_id}): {line.quantity:g} {line.unit}")
    return "\n".join(parts)
