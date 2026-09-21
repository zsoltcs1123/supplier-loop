from __future__ import annotations

import re

from supplier_loop.extract.schema import ExtractRequest, ExtractResult
from supplier_loop.round_state.models import QuoteLine

_QTY_LINE = re.compile(
    r"qty\s+([0-9][0-9.,]*)\s+(.+?)\s+([0-9][0-9.,]*)\s+USD",
    re.IGNORECASE,
)
_BULLET_LINE = re.compile(
    r"^[-*]\s+([0-9][0-9.,]*)\s+(\S+)\s+(.+?)\s+@\s+\$?\s*([0-9][0-9.,]*)\s+USD",
    re.IGNORECASE,
)
_COLON_PRICE_QTY = re.compile(
    r"^[•\-\*]?\s*(.+?):\s+\$?\s*([0-9][0-9.,]*)\s*(?:USD)?\s*/\S+\s+[x×]\s+"
    r"([0-9][0-9.,]*)\b",
    re.IGNORECASE,
)
_COLON_QTY_PRICE = re.compile(
    r"^[•\-\*]?\s*(.+?):\s+qty\s+([0-9][0-9.,]*)\s+\S+\s+[x×]\s+\$?\s*"
    r"([0-9][0-9.,]*)",
    re.IGNORECASE,
)
_SKU = re.compile(r"\(([^)]+)\)\s*$")
_NET = re.compile(r"\bNet\s+(\d+)\b", re.IGNORECASE)
_VALID = re.compile(r"\bvalid(?:ity)?[^\d]{0,24}(\d+)\s*days", re.IGNORECASE)
_TOTAL = re.compile(
    r"^Total\b[^\d$]{0,40}\$?\s*([0-9][0-9.,]*)",
    re.IGNORECASE | re.MULTILINE,
)


class CrudeExtractor:
    def extract(self, request: ExtractRequest) -> ExtractResult:
        lines = _parse_lines(request.body)
        payment = _first_int(_NET, request.body)
        validity = _first_int(_VALID, request.body)
        stated = _first_decimal(_TOTAL, request.body)
        totals = [line.total for line in lines]
        grand = stated if stated is not None else sum(totals)
        return ExtractResult(
            line_items=lines,
            payment_terms=f"Net {payment}" if payment is not None else "",
            validity_days=validity if validity is not None else 0,
            grand_total=grand,
            injection_suspected=False,
        )


def _parse_lines(body: str) -> list[QuoteLine]:
    colon_price: list[QuoteLine] = []
    colon_qty: list[QuoteLine] = []
    bullets: list[QuoteLine] = []
    qty: list[QuoteLine] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith(">"):
            continue
        if match := _COLON_PRICE_QTY.match(line):
            colon_price.append(_colon_price_qty_line(match))
            continue
        if match := _COLON_QTY_PRICE.match(line):
            colon_qty.append(_colon_qty_price_line(match))
            continue
        if match := _BULLET_LINE.match(line):
            bullets.append(_bullet_line(match))
            continue
        if match := _QTY_LINE.search(line):
            qty.append(_qty_line(match))
    if colon_price:
        return colon_price
    if colon_qty:
        return colon_qty
    if bullets:
        return bullets
    return qty


def _colon_price_qty_line(match: re.Match[str]) -> QuoteLine:
    return _quote_line(
        description=match.group(1).strip(),
        quantity=parse_decimal(match.group(3)),
        unit_price=parse_decimal(match.group(2)),
    )


def _colon_qty_price_line(match: re.Match[str]) -> QuoteLine:
    return _quote_line(
        description=match.group(1).strip(),
        quantity=parse_decimal(match.group(2)),
        unit_price=parse_decimal(match.group(3)),
    )


def _bullet_line(match: re.Match[str]) -> QuoteLine:
    return _quote_line(
        description=match.group(3).strip(),
        quantity=parse_decimal(match.group(1)),
        unit_price=parse_decimal(match.group(4)),
    )


def _qty_line(match: re.Match[str]) -> QuoteLine:
    return _quote_line(
        description=match.group(2).strip(),
        quantity=parse_decimal(match.group(1)),
        unit_price=parse_decimal(match.group(3)),
        parse_sku=False,
    )


def _quote_line(
    *,
    description: str,
    quantity: float,
    unit_price: float,
    parse_sku: bool = True,
) -> QuoteLine:
    material_id: str | None = None
    resolved = description
    if parse_sku:
        sku_match = _SKU.search(description)
        if sku_match:
            material_id = sku_match.group(1)
            resolved = description[: sku_match.start()].strip()
    total = round(quantity * unit_price, 2)
    return QuoteLine(
        material_id=material_id,
        description=resolved,
        quantity=quantity,
        unit_price=unit_price,
        total=total,
    )


def parse_decimal(raw: str) -> float:
    text = raw.strip().replace(" ", "").replace("$", "")
    if "," in text and "." in text:
        if text.rindex(",") > text.rindex("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        _left, right = text.rsplit(",", 1)
        if len(right) == 3 and _left.replace(",", "").isdigit():
            text = text.replace(",", "")
        else:
            text = text.replace(",", ".")
    return float(text)


def _first_int(pattern: re.Pattern[str], body: str) -> int | None:
    match = pattern.search(body)
    if match is None:
        return None
    return int(match.group(1))


def _first_decimal(pattern: re.Pattern[str], body: str) -> float | None:
    match = pattern.search(body)
    if match is None:
        return None
    return parse_decimal(match.group(1))
