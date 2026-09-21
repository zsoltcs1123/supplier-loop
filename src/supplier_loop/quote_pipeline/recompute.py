from collections.abc import Sequence


def recomputed_line_total(quantity: float, unit_price: float) -> float:
    return quantity * unit_price


def recomputed_grand_total(line_totals: Sequence[float]) -> float:
    return float(sum(line_totals))
