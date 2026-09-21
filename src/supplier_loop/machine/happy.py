from datetime import UTC, datetime
from typing import TextIO

from supplier_loop.classer.classify import required_classes
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


def advance_quoted_suppliers(state: RoundState) -> None:
    for supplier_id in relevant_supplier_ids(state):
        supplier = state.suppliers[supplier_id]
        if supplier.phase != "quoted":
            continue
        _apply_classer(supplier, state)


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


def mark_quote_received(supplier: SupplierFacts) -> None:
    if supplier.phase in {"idle", "rfq_sent", "awaiting_quote"}:
        supplier.phase = "quoted"


def _apply_classer(supplier: SupplierFacts, state: RoundState) -> None:
    if supplier.quote is None:
        return
    classes = required_classes(
        supplier.quote,
        state.rfq,
        supplier_id=supplier.supplier_id,
        injection_suspected=supplier.injection_suspected,
        own_quote_history=supplier.own_quote_history,
    )
    supplier.escalation_classes = sorted(classes)
    if not classes:
        supplier.phase = "done"


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
