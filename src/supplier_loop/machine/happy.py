from datetime import UTC, datetime
from typing import TextIO

from supplier_loop.operational_log.log import LogEvent, OperationalLog
from supplier_loop.orchestrator.relevance import bom_lines_for_supplier, relevant_supplier_ids
from supplier_loop.progress import emit_progress
from supplier_loop.round_state.models import RoundState, SupplierFacts
from supplier_loop.simulator.port import Assignment, BomLine, Simulator


def send_pending_rfqs(
    state: RoundState,
    simulator: Simulator,
    log: OperationalLog,
    *,
    progress: TextIO | None = None,
) -> None:
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
    supplier.phase = "awaiting_quote"
    supplier.awaiting_since_sim_time = state.rfq.clock.sim_time_seconds
    sim_time = state.rfq.clock.sim_time_seconds
    if progress is not None:
        emit_progress(
            progress,
            sim_time_seconds=sim_time,
            kind="rfq_sent",
            subject=f"{supplier.supplier_id} {email_id}",
        )
    log.append(
        LogEvent(
            wall_time=datetime.now(UTC),
            sim_time_seconds=sim_time,
            kind="rfq_sent",
            detail={"supplier_id": supplier.supplier_id, "email_id": email_id},
        )
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
