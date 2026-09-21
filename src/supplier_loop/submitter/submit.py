from supplier_loop.machine.constants import QUIET_MARGIN_SIM_SECONDS
from supplier_loop.machine.ruling import is_approval_ruling
from supplier_loop.quote_pipeline.recompute import recomputed_line_total
from supplier_loop.relevance import relevant_supplier_ids
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
        return _has_approver_approval(supplier)
    return not supplier.escalation_classes


def build_submit_entry(
    supplier: SupplierFacts,
    sent: list[SentEmailRecord],
    approver_email: str,
) -> SubmitEntry:
    quote = supplier.quote
    if quote is None:
        raise ValueError(f"missing quote for {supplier.supplier_id}")
    document = quote.revised_as_sent or quote.as_sent
    line_items = [
        SubmitLineItem(
            material_id=line.material_id or "",
            quantity=line.quantity,
            unit_price=line.unit_price,
            total=recomputed_line_total(line.quantity, line.unit_price),
        )
        for line in document.line_items
    ]
    return SubmitEntry(
        line_items=line_items,
        payment_terms=document.payment_terms,
        validity_days=document.validity_days,
        grand_total=quote.recomputed_grand_total,
        action_taken=derive_action_taken(supplier, sent, approver_email),
        auto_approved=derive_auto_approved(supplier, sent, approver_email),
    )


def build_reminded_entry(
    supplier: SupplierFacts,
    sent: list[SentEmailRecord],
    approver_email: str,
) -> SubmitEntry:
    return SubmitEntry(
        line_items=[],
        payment_terms="",
        validity_days=0,
        grand_total=0.0,
        action_taken=derive_action_taken(supplier, sent, approver_email),
        auto_approved=False,
    )


def build_submit_payload(state: RoundState, simulator: Simulator) -> dict[str, SubmitEntry]:
    sent = simulator.list_sent()
    approver_email = state.rfq.assignment.approver_email
    payload: dict[str, SubmitEntry] = {}
    for supplier_id in sorted(relevant_supplier_ids(state)):
        supplier = state.suppliers[supplier_id]
        if not _supplier_ready_for_submit(supplier):
            continue
        if supplier.quote is None:
            payload[supplier_id] = build_reminded_entry(supplier, sent, approver_email)
            continue
        payload[supplier_id] = build_submit_entry(supplier, sent, approver_email)
    return payload


def round_ready_to_submit(state: RoundState) -> bool:
    relevant = relevant_supplier_ids(state)
    if not relevant:
        return False
    any_silent = False
    sim_time = state.rfq.clock.sim_time_seconds
    for supplier_id in relevant:
        supplier = state.suppliers[supplier_id]
        if not _supplier_ready_for_submit(supplier):
            return False
        if supplier.reminder_sim_time is not None and supplier.quote is None:
            any_silent = True
            if sim_time - supplier.reminder_sim_time < QUIET_MARGIN_SIM_SECONDS:
                return False
    return (not any_silent) or _inbox_quiet(state)


def _inbox_quiet(state: RoundState) -> bool:
    if any(entry.id not in state.dedup.email_ids for entry in state.inbox):
        return False
    last_inbound = 0.0
    for entry in state.inbox:
        last_inbound = max(last_inbound, entry.sim_time_hours * 3600.0)
    if last_inbound == 0.0:
        return True
    return state.rfq.clock.sim_time_seconds - last_inbound >= QUIET_MARGIN_SIM_SECONDS


def _supplier_ready_for_submit(supplier: SupplierFacts) -> bool:
    if supplier.phase == "done" and supplier.quote is not None:
        return True
    if supplier.reminder_sim_time is not None and supplier.quote is None:
        return True
    return supplier.phase == "escalated" and supplier.quote is not None


def _has_approver_approval(supplier: SupplierFacts) -> bool:
    if not supplier.approver_rulings:
        return False
    return is_approval_ruling(supplier.approver_rulings[-1])


def _has_escalation_mail(
    supplier_id: str,
    sent: list[SentEmailRecord],
    approver_email: str,
) -> bool:
    ref = f"[REF:{supplier_id}]"
    return any(mail.to == approver_email and ref in mail.subject for mail in sent)
