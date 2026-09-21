from supplier_loop.relevance import bom_lines_for_supplier
from supplier_loop.round_state.models import AsSentQuote, RoundState


def missing_lines(quote_as_sent: AsSentQuote, state: RoundState, supplier_id: str) -> list[str]:
    catalog = {line.material_id for line in bom_lines_for_supplier(state, supplier_id)}
    quoted = {line.material_id for line in quote_as_sent.line_items if line.material_id is not None}
    return sorted(material_id for material_id in catalog if material_id not in quoted)


def quantity_mismatches(
    quote_as_sent: AsSentQuote, state: RoundState, supplier_id: str
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


def bom_quantity(state: RoundState, supplier_id: str, material_id: str) -> float:
    for bom_line in bom_lines_for_supplier(state, supplier_id):
        if bom_line.material_id == material_id:
            return bom_line.quantity
    return 0.0
