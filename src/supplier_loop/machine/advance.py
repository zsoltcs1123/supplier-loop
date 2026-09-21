from supplier_loop.classer.classify import required_classes
from supplier_loop.machine.escalate import send_pending_escalations
from supplier_loop.machine.negotiate import negotiate_once
from supplier_loop.relevance import relevant_supplier_ids
from supplier_loop.round_state.models import RoundState, SupplierFacts
from supplier_loop.simulator.port import Simulator

_SENDABLE_CLASSES = (1, 2, 3, 4, 7, 6)


def advance_suppliers(state: RoundState, simulator: Simulator) -> None:
    sent = simulator.list_sent()
    for supplier_id in relevant_supplier_ids(state):
        supplier = state.suppliers[supplier_id]
        if supplier.phase not in {"quoted", "escalated"} or supplier.quote is None:
            continue
        _apply_classer(supplier, state)
        classes = _with_last_rejection(supplier)
        if 5 in classes and not supplier.negotiation_used:
            negotiate_once(supplier, state, simulator)
            _apply_classer(supplier, state)
            classes = _with_last_rejection(supplier)
            sent = simulator.list_sent()
        sendable = [class_num for class_num in _SENDABLE_CLASSES if class_num in classes]
        waiting_for_reply = (
            5 in classes and supplier.negotiation_used and not supplier.own_quote_history
        )
        if sendable:
            send_pending_escalations(supplier, state, simulator, sent)
            sent = simulator.list_sent()
            supplier.phase = "escalated"
        elif waiting_for_reply:
            continue
        elif supplier.phase != "done":
            supplier.phase = "done"


def mark_quote_received(supplier: SupplierFacts, *, sim_time_days: float) -> None:
    if supplier.phase in {"idle", "rfq_sent", "awaiting_quote"}:
        supplier.phase = "quoted"
    supplier.quote_received_sim_days = sim_time_days


def _with_last_rejection(supplier: SupplierFacts) -> list[int]:
    classes = list(supplier.escalation_classes)
    if (
        supplier.quote is not None
        and supplier.quote.revised_as_sent is not None
        and supplier.last_rejection_class is not None
        and supplier.last_rejection_class not in classes
    ):
        classes.append(supplier.last_rejection_class)
        supplier.escalation_classes = sorted(classes)
        return list(supplier.escalation_classes)
    return classes


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
