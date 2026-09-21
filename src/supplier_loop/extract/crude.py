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
    re.IGNORECASE | re.MULTILINE,
)
_SKU = re.compile(r"\(([^)]+)\)\s*$")
_NET = re.compile(r"\bNet\s+(\d+)\b", re.IGNORECASE)
_VALID = re.compile(r"\bvalid(?:ity)?[^\d]{0,24}(\d+)\s*days", re.IGNORECASE)
_TOTAL = re.compile(
    r"^Total\b[^\d$]{0,40}\$?\s*([0-9][0-9.,]*)",
    re.MULTILINE,
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
    bullets = [_bullet_line(match) for match in _BULLET_LINE.finditer(body)]
    if bullets:
        return bullets
    return [_qty_line(match) for match in _QTY_LINE.finditer(body)]


def _bullet_line(match: re.Match[str]) -> QuoteLine:
    quantity = parse_decimal(match.group(1))
    description = match.group(3).strip()
    unit_price = parse_decimal(match.group(4))
    sku_match = _SKU.search(description)
    material_id = sku_match.group(1) if sku_match else None
    if sku_match:
        description = description[: sku_match.start()].strip()
    total = round(quantity * unit_price, 2)
    return QuoteLine(
        material_id=material_id,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        total=total,
    )


def _qty_line(match: re.Match[str]) -> QuoteLine:
    quantity = parse_decimal(match.group(1))
    description = match.group(2).strip()
    unit_price = parse_decimal(match.group(3))
    total = round(quantity * unit_price, 2)
    return QuoteLine(
        material_id=None,
        description=description,
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
