import re
from collections.abc import Mapping, Sequence

from supplier_loop.round_state.models import QuoteLine, RfqContext

_TRAILING_PARENS = re.compile(r"\s*\([^)]*\)\s*$")


def description_catalog(rfq: RfqContext) -> dict[str, str]:
    grouped: dict[str, set[str]] = {}
    for material_id, description in _catalog_pairs(rfq):
        key = canonical_description(description)
        grouped.setdefault(key, set()).add(material_id)
    return {key: next(iter(ids)) for key, ids in grouped.items() if len(ids) == 1}


def canonical_description(description: str) -> str:
    stripped = _TRAILING_PARENS.sub("", description)
    return " ".join(stripped.casefold().split())


def normalize_quote_line(line: QuoteLine, catalog: Mapping[str, str]) -> QuoteLine:
    if line.material_id:
        return line.model_copy(deep=True)
    material_id = catalog.get(canonical_description(line.description))
    return line.model_copy(deep=True, update={"material_id": material_id})


def _catalog_pairs(rfq: RfqContext) -> Sequence[tuple[str, str]]:
    pairs: list[tuple[str, str]] = [
        (line.material_id, line.description) for line in rfq.assignment.line_items
    ]
    pairs.extend((row.material_id, row.description) for row in rfq.price_history)
    return pairs
