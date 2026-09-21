from supplier_loop.orchestrator.relevance import relevant_supplier_ids
from supplier_loop.quote_pipeline.recompute import recomputed_line_total
from supplier_loop.round_state.models import RoundState, SupplierFacts
from supplier_loop.simulator.port import SentEmailRecord, Simulator, SubmitEntry, SubmitLineItem


def derive_action_taken(
    supplier: SupplierFacts,
    sent: list[SentEmailRecord],
    approver_email: str,
) -> str:
    if _has_escalation_mail(supplier.supplier_id, sent, approver_email):
        return "escalated"
    if supplier.question_answered:
        return "answered_question"
    if supplier.reminder_sim_time is not None:
        return "reminded"
    return "extract"


def derive_auto_approved(
    supplier: SupplierFacts,
    sent: list[SentEmailRecord],
    approver_email: str,
) -> bool:
    if _has_escalation_mail(supplier.supplier_id, sent, approver_email):
        return False
    return not supplier.escalation_classes


def build_submit_entry(
    supplier: SupplierFacts,
    sent: list[SentEmailRecord],
    approver_email: str,
) -> SubmitEntry:
    quote = supplier.quote
    if quote is None:
        raise ValueError(f"missing quote for {supplier.supplier_id}")
    as_sent = quote.as_sent
    line_items = [
        SubmitLineItem(
            material_id=line.material_id or "",
            quantity=line.quantity,
            unit_price=line.unit_price,
            total=recomputed_line_total(line.quantity, line.unit_price),
        )
        for line in as_sent.line_items
    ]
    return SubmitEntry(
        line_items=line_items,
        payment_terms=as_sent.payment_terms,
        validity_days=as_sent.validity_days,
        grand_total=quote.recomputed_grand_total,
        action_taken=derive_action_taken(supplier, sent, approver_email),
        auto_approved=derive_auto_approved(supplier, sent, approver_email),
    )


def build_submit_payload(state: RoundState, simulator: Simulator) -> dict[str, SubmitEntry]:
    sent = simulator.list_sent()
    approver_email = state.rfq.assignment.approver_email
    payload: dict[str, SubmitEntry] = {}
    for supplier_id in sorted(relevant_supplier_ids(state)):
        supplier = state.suppliers[supplier_id]
        if supplier.phase != "done" or supplier.quote is None:
            continue
        payload[supplier_id] = build_submit_entry(supplier, sent, approver_email)
    return payload


def round_ready_to_submit(state: RoundState) -> bool:
    relevant = relevant_supplier_ids(state)
    if not relevant:
        return False
    for supplier_id in relevant:
        supplier = state.suppliers[supplier_id]
        if supplier.phase != "done" or supplier.quote is None:
            return False
    return True


def _has_escalation_mail(
    supplier_id: str,
    sent: list[SentEmailRecord],
    approver_email: str,
) -> bool:
    ref = f"[REF:{supplier_id}]"
    return any(mail.to == approver_email and ref in mail.subject for mail in sent)
