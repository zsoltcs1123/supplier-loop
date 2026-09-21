from datetime import UTC, datetime
from typing import TextIO

from supplier_loop.machine.constants import REMINDER_THRESHOLD_SIM_SECONDS
from supplier_loop.operational_log.log import LogEvent, OperationalLog
from supplier_loop.orchestrator.relevance import relevant_supplier_ids
from supplier_loop.progress import emit_progress
from supplier_loop.round_state.models import RoundState, SupplierFacts
from supplier_loop.simulator.port import Simulator


def send_due_reminders(
    state: RoundState,
    simulator: Simulator,
    log: OperationalLog,
    *,
    progress: TextIO | None = None,
) -> None:
    sim_time = state.rfq.clock.sim_time_seconds
    for supplier_id in relevant_supplier_ids(state):
        supplier = state.suppliers[supplier_id]
        if not _needs_reminder(supplier, sim_time):
            continue
        subject = f"Reminder: {state.rfq.assignment.rfq_id}"
        body = (
            f"Following up on our RFQ {state.rfq.assignment.rfq_id}. "
            f"Please send your quote when ready."
        )
        email_id = simulator.send_email(supplier.email, subject, body)
        supplier.outbound_ids.append(email_id)
        supplier.reminder_sim_time = sim_time
        if progress is not None:
            emit_progress(
                progress,
                sim_time_seconds=sim_time,
                kind="reminder_due",
                subject=f"{supplier_id} reminder_due",
            )
        log.append(
            LogEvent(
                wall_time=datetime.now(UTC),
                sim_time_seconds=sim_time,
                kind="reminder_due",
                detail={"supplier_id": supplier_id, "email_id": email_id},
            )
        )


def _needs_reminder(supplier: SupplierFacts, sim_time: float) -> bool:
    if supplier.reminder_sim_time is not None:
        return False
    if supplier.phase not in {"awaiting_quote", "rfq_sent"}:
        return False
    if supplier.awaiting_since_sim_time is None:
        return False
    return sim_time - supplier.awaiting_since_sim_time >= REMINDER_THRESHOLD_SIM_SECONDS
