from supplier_loop.machine.discrepancy import bom_quantity, missing_lines, quantity_mismatches
from supplier_loop.round_state.models import RoundState, SupplierFacts
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
        missing = missing_lines(as_sent, state, supplier.supplier_id)
        return (
            f"Please add the missing line(s) to your quote: {', '.join(missing)}. "
            f"Resend the revised quote in this thread."
        )
    if class_num == 2:
        mismatches = quantity_mismatches(as_sent, state, supplier.supplier_id)
        parts = []
        for material_id, quoted_qty in mismatches:
            bom_qty = bom_quantity(state, supplier.supplier_id, material_id)
            parts.append(f"{material_id} must be {bom_qty:g} not {quoted_qty:g}")
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
