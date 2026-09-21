from supplier_loop.orchestrator.relevance import bom_lines_for_supplier
from supplier_loop.round_state.models import AsSentQuote, RoundState, SupplierFacts
from supplier_loop.simulator.port import Simulator


def correct_once(
    supplier: SupplierFacts,
    state: RoundState,
    simulator: Simulator,
    class_num: int,
) -> bool:
    if supplier.correction_used or supplier.quote is None:
        return False
    body = _correction_body(class_num, supplier, state)
    subject = f"Correction needed for {state.rfq.assignment.rfq_id}"
    email_id = simulator.send_email(supplier.email, subject, body)
    supplier.outbound_ids.append(email_id)
    supplier.correction_used = True
    return True


def _correction_body(class_num: int, supplier: SupplierFacts, state: RoundState) -> str:
    assignment = state.rfq.assignment
    as_sent = supplier.quote.as_sent if supplier.quote is not None else None
    if supplier.quote is not None and supplier.quote.revised_as_sent is not None:
        as_sent = supplier.quote.revised_as_sent
    if as_sent is None:
        return "Please correct your quote and resend it in this thread."
    if class_num == 1:
        missing = _missing_lines(as_sent, state, supplier.supplier_id)
        return (
            f"Please add the missing line(s) to your quote: {', '.join(missing)}. "
            f"Resend the revised quote in this thread."
        )
    if class_num == 2:
        mismatches = _quantity_mismatches(as_sent, state, supplier.supplier_id)
        parts = [
            f"{material_id} must be {bom_qty:g} not {quoted_qty:g}"
            for material_id, quoted_qty in mismatches
            for bom_qty in [_bom_quantity(state, supplier.supplier_id, material_id)]
        ]
        return (
            f"Please correct quantity on: {'; '.join(parts)}. "
            f"Resend the revised quote in this thread."
        )
    if class_num == 3:
        return (
            f"Please update payment terms to {assignment.required_payment_terms}. "
            f"Resend the revised quote in this thread."
        )
    if class_num == 4:
        return (
            f"Please extend validity to at least {assignment.required_validity_days} days. "
            f"Resend the revised quote in this thread."
        )
    return "Please correct your quote and resend it in this thread."


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


def _bom_quantity(state: RoundState, supplier_id: str, material_id: str) -> float:
    for bom_line in bom_lines_for_supplier(state, supplier_id):
        if bom_line.material_id == material_id:
            return bom_line.quantity
    return 0.0
