from supplier_loop.machine.due import due_alarms
from supplier_loop.relevance import relevant_supplier_ids
from supplier_loop.round_state.models import RoundState


def should_run_pass(state: RoundState) -> bool:
    if due_alarms(state):
        return True
    if _has_inbox_delta(state):
        return True
    if _has_empty_quote(state):
        return True
    return _has_idle_relevant_supplier(state)


def _has_inbox_delta(state: RoundState) -> bool:
    return any(entry.id not in state.dedup.email_ids for entry in state.inbox)


def _has_idle_relevant_supplier(state: RoundState) -> bool:
    for supplier_id in relevant_supplier_ids(state):
        if state.suppliers[supplier_id].phase == "idle":
            return True
    return False


def _has_empty_quote(state: RoundState) -> bool:
    for supplier_id in relevant_supplier_ids(state):
        quote = state.suppliers[supplier_id].quote
        if quote is not None and not quote.as_sent.line_items:
            return True
    return False
