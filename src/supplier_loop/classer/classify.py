from supplier_loop.round_state.models import AsSentQuote, QuoteLine, QuoteRecord, RfqContext
from supplier_loop.simulator.port import BomLine, PriceHistoryRow, SupplierEntry


def required_classes(
    quote: QuoteRecord,
    rfq: RfqContext,
    *,
    supplier_id: str,
    injection_suspected: bool,
    own_quote_history: list[AsSentQuote],
) -> frozenset[int]:
    classes: set[int] = set()
    as_sent = _effective_as_sent(quote)
    assignment = rfq.assignment
    catalog = _supplier_material_ids(rfq.directory, supplier_id)

    if _has_missing_bom_line(as_sent.line_items, assignment.line_items, catalog):
        classes.add(1)
    if _has_quantity_mismatch(as_sent.line_items, assignment.line_items, catalog):
        classes.add(2)
    if as_sent.payment_terms != assignment.required_payment_terms:
        classes.add(3)
    if as_sent.validity_days < assignment.required_validity_days:
        classes.add(4)
    if _has_price_above_ceiling(
        as_sent.line_items,
        rfq.price_history,
        supplier_id,
        assignment.target_price_ceiling_pct,
    ):
        classes.add(5)
    if own_quote_history:
        classes.add(6)
    if injection_suspected:
        classes.add(7)

    return frozenset(classes)


def _effective_as_sent(quote: QuoteRecord) -> AsSentQuote:
    if quote.revised_as_sent is not None:
        return quote.revised_as_sent
    return quote.as_sent


def _supplier_material_ids(directory: list[SupplierEntry], supplier_id: str) -> set[str]:
    for entry in directory:
        if entry.supplier_id == supplier_id:
            return set(entry.material_ids)
    return set()


def _quote_lines_by_material(line_items: list[QuoteLine]) -> dict[str, QuoteLine]:
    return {line.material_id: line for line in line_items if line.material_id is not None}


def _has_missing_bom_line(
    quote_lines: list[QuoteLine],
    bom_lines: list[BomLine],
    catalog: set[str],
) -> bool:
    quoted_material_ids = {line.material_id for line in quote_lines if line.material_id is not None}
    for bom_line in bom_lines:
        if bom_line.material_id in catalog and bom_line.material_id not in quoted_material_ids:
            return True
    return False


def _has_quantity_mismatch(
    quote_lines: list[QuoteLine],
    bom_lines: list[BomLine],
    catalog: set[str],
) -> bool:
    quote_by_material = _quote_lines_by_material(quote_lines)
    for bom_line in bom_lines:
        if bom_line.material_id not in catalog:
            continue
        quote_line = quote_by_material.get(bom_line.material_id)
        if quote_line is None:
            continue
        if quote_line.quantity != bom_line.quantity:
            return True
    return False


def _has_price_above_ceiling(
    quote_lines: list[QuoteLine],
    price_history: list[PriceHistoryRow],
    supplier_id: str,
    target_price_ceiling_pct: float,
) -> bool:
    history_by_material = {
        row.material_id: row.last_accepted_unit_price
        for row in price_history
        if row.supplier_id == supplier_id
    }
    for line in quote_lines:
        if line.material_id is None:
            continue
        last_accepted = history_by_material.get(line.material_id)
        if last_accepted is None:
            continue
        ceiling = last_accepted * (1 + target_price_ceiling_pct / 100)
        if line.unit_price > ceiling:
            return True
    return False
