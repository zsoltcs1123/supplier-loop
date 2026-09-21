from supplier_loop.quote_pipeline.recompute import recomputed_grand_total, recomputed_line_total
from supplier_loop.round_state.models import AsSentQuote, RoundState, SupplierFacts
from supplier_loop.simulator.port import Simulator


def negotiate_once(
    supplier: SupplierFacts,
    state: RoundState,
    simulator: Simulator,
) -> bool:
    if supplier.quote is None or supplier.own_quote_history:
        return False
    target_total = compute_target_total(supplier, state)
    body = f"Your price is above our ceiling. We can do {target_total:,.2f} total for this quote."
    subject = f"Counter-offer for {state.rfq.assignment.rfq_id}"
    email_id = simulator.send_email(supplier.email, subject, body)
    supplier.outbound_ids.append(email_id)
    supplier.own_quote_history.append(supplier.quote.as_sent.model_copy(deep=True))
    return True


def compute_target_total(supplier: SupplierFacts, state: RoundState) -> float:
    quote = supplier.quote
    if quote is None:
        return 0.0
    ceiling_pct = state.rfq.assignment.target_price_ceiling_pct
    history = {
        row.material_id: row.last_accepted_unit_price
        for row in state.rfq.price_history
        if row.supplier_id == supplier.supplier_id
    }
    line_totals: list[float] = []
    for line in quote.as_sent.line_items:
        if line.material_id is None:
            unit_price = line.unit_price
        else:
            last_accepted = history.get(line.material_id, line.unit_price)
            unit_price = last_accepted * (1 + ceiling_pct / 100)
        line_totals.append(recomputed_line_total(line.quantity, unit_price))
    return recomputed_grand_total(line_totals)


def record_negotiation_reply(supplier: SupplierFacts, reply: AsSentQuote | None = None) -> None:
    if supplier.quote is None:
        return
    if reply is not None:
        supplier.own_quote_history.append(reply)
    elif not supplier.own_quote_history:
        supplier.own_quote_history.append(supplier.quote.as_sent.model_copy(deep=True))
