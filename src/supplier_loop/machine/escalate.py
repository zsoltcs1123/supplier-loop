from supplier_loop.machine.discrepancy import missing_lines, quantity_mismatches
from supplier_loop.round_state.models import AsSentQuote, RoundState, SupplierFacts
from supplier_loop.simulator.port import Assignment, SentEmailRecord, Simulator


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
        body = _escalation_body(class_num, supplier, state, revised=revised)
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
    supplier: SupplierFacts,
    state: RoundState,
    *,
    revised: bool = False,
) -> str:
    quote = supplier.quote
    if quote is None:
        return f"{_class_marker(class_num, revised=revised)} discrepancy requires approver review."
    as_sent = quote.revised_as_sent or quote.as_sent
    assignment = state.rfq.assignment
    marker = _class_marker(class_num, revised=revised)
    specific = _class_specific_claim(class_num, as_sent, state, supplier)
    if revised:
        return f"{marker} {specific} {_quote_now_on_file(as_sent, assignment)}"
    return f"{marker} {specific}"


def _class_specific_claim(
    class_num: int,
    as_sent: AsSentQuote,
    state: RoundState,
    supplier: SupplierFacts,
) -> str:
    assignment = state.rfq.assignment
    if class_num == 1:
        return _class_1_claim(as_sent, state, supplier.supplier_id)
    if class_num == 2:
        return _class_2_claim(as_sent, state, supplier.supplier_id)
    if class_num == 3:
        return (
            f"payment terms {as_sent.payment_terms!r} "
            f"differs from required {assignment.required_payment_terms!r}."
        )
    if class_num == 4:
        return (
            f"validity {as_sent.validity_days} days "
            f"is shorter than required {assignment.required_validity_days} days."
        )
    if class_num == 6:
        return _class_6_claim(supplier)
    if class_num == 7:
        return "supplier content contains embedded instructions."
    return "discrepancy requires approver review."


def _class_1_claim(as_sent: AsSentQuote, state: RoundState, supplier_id: str) -> str:
    missing = missing_lines(as_sent, state, supplier_id)
    if missing:
        return f"missing BOM line(s): {', '.join(missing)}."
    return "required BOM lines are present."


def _class_2_claim(as_sent: AsSentQuote, state: RoundState, supplier_id: str) -> str:
    mismatches = quantity_mismatches(as_sent, state, supplier_id)
    if mismatches:
        parts = [f"{material_id} quoted {qty:g}" for material_id, qty in mismatches]
        return f"quantity mismatch on {', '.join(parts)}."
    return "quoted quantities match the BOM."


def _class_6_claim(supplier: SupplierFacts) -> str:
    original = supplier.quote.recomputed_grand_total if supplier.quote is not None else 0.0
    parts = [f"original {original:,.2f}"]
    if supplier.negotiation_target_total is not None:
        parts.append(f"counter {supplier.negotiation_target_total:,.2f}")
    if supplier.negotiation_reply_total is not None:
        parts.append(f"supplier reply {supplier.negotiation_reply_total:,.2f}")
    return "negotiation outcome " + ", ".join(parts) + "."


def _quote_now_on_file(as_sent: AsSentQuote, assignment: Assignment) -> str:
    lines = (
        ", ".join(
            f"{line.material_id or line.description} qty {line.quantity:g} at {line.unit_price:g}"
            for line in as_sent.line_items
        )
        or "no lines"
    )
    return (
        f"Quote now on file: {lines}; "
        f"terms {as_sent.payment_terms!r} (required {assignment.required_payment_terms!r}); "
        f"validity {as_sent.validity_days} days (required {assignment.required_validity_days})."
    )
