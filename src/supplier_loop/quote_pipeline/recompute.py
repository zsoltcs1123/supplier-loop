from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

_CENTS = Decimal("0.01")


def recomputed_line_total(quantity: float, unit_price: float) -> float:
    return _to_cents(_money(quantity) * _money(unit_price))


def recomputed_grand_total(line_totals: Sequence[float]) -> float:
    total = sum((_money(line) for line in line_totals), start=Decimal(0))
    return _to_cents(total)


def _money(value: float) -> Decimal:
    return Decimal(str(value))


def _to_cents(amount: Decimal) -> float:
    return float(amount.quantize(_CENTS, rounding=ROUND_HALF_UP))
