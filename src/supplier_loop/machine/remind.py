from typing import TextIO

from supplier_loop.machine.due import reminder_is_due
from supplier_loop.operational_log.log import OperationalLog
from supplier_loop.progress import emit_progress
from supplier_loop.relevance import relevant_supplier_ids
from supplier_loop.round_state.models import RoundState
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
        if not reminder_is_due(supplier, sim_time):
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
        log.record(
            round_id=state.rfq.clock.round_id,
            sim_time_seconds=sim_time,
            kind="reminder_due",
            detail={"supplier_id": supplier_id, "email_id": email_id},
        )
