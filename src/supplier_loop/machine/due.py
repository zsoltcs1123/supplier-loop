from supplier_loop.machine.constants import (
    REMINDER_THRESHOLD_SIM_SECONDS,
    VALIDITY_ALARM_MARGIN_DAYS,
)
from supplier_loop.relevance import relevant_supplier_ids
from supplier_loop.round_state.models import RoundState, SupplierFacts


def due_alarms(state: RoundState) -> list[str]:
    alarms: list[str] = []
    if _has_reminder_due(state):
        alarms.append("reminder_due")
    if _has_validity_alarm(state):
        alarms.append("validity_alarm")
    return alarms


def reminder_is_due(supplier: SupplierFacts, sim_time: float) -> bool:
    if supplier.reminder_sim_time is not None:
        return False
    if supplier.phase not in {"awaiting_quote", "rfq_sent"}:
        return False
    if supplier.awaiting_since_sim_time is None:
        return False
    return sim_time - supplier.awaiting_since_sim_time >= REMINDER_THRESHOLD_SIM_SECONDS


def _has_reminder_due(state: RoundState) -> bool:
    sim_time = state.rfq.clock.sim_time_seconds
    for supplier_id in relevant_supplier_ids(state):
        supplier = state.suppliers[supplier_id]
        if reminder_is_due(supplier, sim_time):
            return True
    return False


def _has_validity_alarm(state: RoundState) -> bool:
    sim_days = state.rfq.clock.sim_time_days
    for supplier_id in relevant_supplier_ids(state):
        supplier = state.suppliers[supplier_id]
        if supplier.phase not in {"quoted", "escalated"} or supplier.quote is None:
            continue
        if supplier.quote_received_sim_days is None:
            continue
        document = supplier.quote.revised_as_sent or supplier.quote.as_sent
        expiry = supplier.quote_received_sim_days + document.validity_days
        if expiry - sim_days <= VALIDITY_ALARM_MARGIN_DAYS:
            return True
    return False
