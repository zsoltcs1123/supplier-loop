from supplier_loop.round_state.models import SupplierFacts

EMPTY_QUOTE_EXTRACT_LIMIT = 2


def awaiting_empty_quote_retry(supplier: SupplierFacts) -> bool:
    quote = supplier.quote
    return (
        quote is not None
        and not quote.as_sent.line_items
        and supplier.empty_extract_count < EMPTY_QUOTE_EXTRACT_LIMIT
    )
