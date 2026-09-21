from supplier_loop.relevance import bom_lines_for_supplier
from supplier_loop.round_state.models import RoundState, SupplierFacts
from supplier_loop.simulator.port import EmailMessage, Simulator


def answer_question(
    supplier: SupplierFacts,
    state: RoundState,
    simulator: Simulator,
    message: EmailMessage,
) -> None:
    if supplier.question_answered:
        return
    assignment = state.rfq.assignment
    lines = bom_lines_for_supplier(state, supplier.supplier_id)
    line_parts = [
        f"{line.description} ({line.material_id}): {line.quantity:g} {line.unit}" for line in lines
    ]
    body = "\n".join(
        [
            f"Payment terms: {assignment.required_payment_terms}.",
            f"Validity: at least {assignment.required_validity_days} days.",
            "",
            "Your RFQ lines:",
            *line_parts,
        ]
    )
    subject = f"Re: {message.subject}"
    email_id = simulator.send_email(supplier.email, subject, body)
    supplier.outbound_ids.append(email_id)
    supplier.question_answered = True
