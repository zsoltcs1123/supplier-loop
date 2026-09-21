from supplier_loop.orchestrator.relevance import bom_lines_for_supplier
from supplier_loop.round_state.models import AsSentQuote, QuoteRecord, RoundState, SupplierFacts
from supplier_loop.simulator.port import SentEmailRecord, Simulator


def send_pending_escalations(
    supplier: SupplierFacts,
    state: RoundState,
    simulator: Simulator,
    sent: list[SentEmailRecord],
) -> None:
    if supplier.quote is None:
        return
    approver = state.rfq.assignment.approver_email
    for class_num in _escalation_classes_to_send(supplier.escalation_classes):
        revised = _use_revised_marker(supplier, class_num)
        if _escalation_sent(supplier.supplier_id, class_num, sent, approver, revised=revised):
            continue
        body = _escalation_body(
            class_num, supplier.quote, state, supplier.supplier_id, revised=revised
        )
        subject = f"[REF:{supplier.supplier_id}] class {class_num}"
        email_id = simulator.send_email(approver, subject, body)
        supplier.outbound_ids.append(email_id)


def _use_revised_marker(supplier: SupplierFacts, class_num: int) -> bool:
    return (
        supplier.correction_used
        and supplier.quote is not None
        and supplier.quote.revised_as_sent is not None
        and class_num in {1, 2, 3, 4}
    )


def _escalation_classes_to_send(classes: list[int]) -> list[int]:
    ordered: list[int] = []
    for class_num in (1, 2, 3, 4, 7, 6):
        if class_num in classes:
            ordered.append(class_num)
    return ordered


def _escalation_sent(
    supplier_id: str,
    class_num: int,
    sent: list[SentEmailRecord],
    approver_email: str,
    *,
    revised: bool = False,
) -> bool:
    ref = f"[REF:{supplier_id}]"
    marker = _class_marker(class_num, revised=revised)
    return any(
        mail.to == approver_email and ref in mail.subject and marker in mail.body for mail in sent
    )


def _class_marker(class_num: int, *, revised: bool = False) -> str:
    if revised:
        return f"Class {class_num} (revised):"
    return f"Class {class_num}:"


def _escalation_body(
    class_num: int,
    quote: QuoteRecord,
    state: RoundState,
    supplier_id: str,
    *,
    revised: bool = False,
) -> str:
    as_sent = quote.revised_as_sent or quote.as_sent
    assignment = state.rfq.assignment
    marker = _class_marker(class_num, revised=revised)
    if class_num == 1:
        missing = _missing_lines(as_sent, state, supplier_id)
        return f"{marker} missing BOM line(s): {', '.join(missing)}."
    if class_num == 2:
        mismatches = _quantity_mismatches(as_sent, state, supplier_id)
        parts = [f"{material_id} quoted {qty:g}" for material_id, qty in mismatches]
        return f"{marker} quantity mismatch on {', '.join(parts)}."
    if class_num == 3:
        return (
            f"{marker} payment terms {as_sent.payment_terms!r} "
            f"differs from required {assignment.required_payment_terms!r}."
        )
    if class_num == 4:
        return (
            f"{marker} validity {as_sent.validity_days} days "
            f"is shorter than required {assignment.required_validity_days} days."
        )
    if class_num == 6:
        return f"{marker} negotiation outcome requires approver sign-off."
    if class_num == 7:
        return f"{marker} supplier content contains embedded instructions."
    return f"{marker} discrepancy requires approver review."


def _missing_lines(quote_as_sent: AsSentQuote, state: RoundState, supplier_id: str) -> list[str]:
    catalog = {line.material_id for line in bom_lines_for_supplier(state, supplier_id)}
    quoted = {line.material_id for line in quote_as_sent.line_items if line.material_id is not None}
    return sorted(material_id for material_id in catalog if material_id not in quoted)


def _quantity_mismatches(
    quote_as_sent: AsSentQuote,
    state: RoundState,
    supplier_id: str,
) -> list[tuple[str, float]]:
    quote_by_material = {
        line.material_id: line.quantity
        for line in quote_as_sent.line_items
        if line.material_id is not None
    }
    mismatches: list[tuple[str, float]] = []
    for bom_line in bom_lines_for_supplier(state, supplier_id):
        quoted_qty = quote_by_material.get(bom_line.material_id)
        if quoted_qty is not None and quoted_qty != bom_line.quantity:
            mismatches.append((bom_line.material_id, quoted_qty))
    return mismatches
