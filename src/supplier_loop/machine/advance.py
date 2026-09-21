from supplier_loop.classer.classify import required_classes
from supplier_loop.machine.escalate import send_pending_escalations
from supplier_loop.machine.negotiate import negotiate_once
from supplier_loop.orchestrator.relevance import relevant_supplier_ids
from supplier_loop.round_state.models import RoundState, SupplierFacts
from supplier_loop.simulator.port import Simulator


def advance_suppliers(state: RoundState, simulator: Simulator) -> None:
    sent = simulator.list_sent()
    for supplier_id in relevant_supplier_ids(state):
        supplier = state.suppliers[supplier_id]
        if supplier.phase not in {"quoted", "escalated"} or supplier.quote is None:
            continue
        _apply_classer(supplier, state)
        classes = list(supplier.escalation_classes)
        if (
            supplier.quote.revised_as_sent is not None
            and supplier.last_rejection_class is not None
            and supplier.last_rejection_class not in classes
        ):
            classes.append(supplier.last_rejection_class)
            supplier.escalation_classes = sorted(classes)
        if classes:
            if 5 in classes and not supplier.own_quote_history:
                negotiate_once(supplier, state, simulator)
                _apply_classer(supplier, state)
                classes = list(supplier.escalation_classes)
                sent = simulator.list_sent()
            send_pending_escalations(supplier, state, simulator, sent)
            sent = simulator.list_sent()
            supplier.phase = "escalated"
        elif supplier.phase != "done":
            supplier.phase = "done"


def mark_quote_received(supplier: SupplierFacts, *, sim_time_days: float) -> None:
    if supplier.phase in {"idle", "rfq_sent", "awaiting_quote"}:
        supplier.phase = "quoted"
    supplier.quote_received_sim_days = sim_time_days


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
