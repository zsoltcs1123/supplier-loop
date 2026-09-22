import pytest

from supplier_loop.classer import required_classes
from supplier_loop.round_state.models import AsSentQuote, QuoteLine, QuoteRecord, RfqContext
from supplier_loop.simulator.port import (
    Assignment,
    BomLine,
    PriceHistoryRow,
    SimClock,
    SupplierEntry,
)


def _clock() -> SimClock:
    return SimClock(
        sim_time_seconds=0.0,
        sim_time_days=0.0,
        round_id="dev-1",
        mode="development",
        clock_factor=60.0,
    )


def _rfq(
    *,
    line_items: list[BomLine] | None = None,
    required_payment_terms: str = "Net 30",
    required_validity_days: int = 14,
    target_price_ceiling_pct: float = 5.0,
    directory: list[SupplierEntry] | None = None,
    price_history: list[PriceHistoryRow] | None = None,
) -> RfqContext:
    return RfqContext(
        assignment=Assignment(
            rfq_id="RFQ-001",
            required_payment_terms=required_payment_terms,
            required_validity_days=required_validity_days,
            target_price_ceiling_pct=target_price_ceiling_pct,
            line_items=line_items
            or [
                BomLine(
                    material_id="STL-BEAM-200",
                    description="Steel I-Beam 200mm",
                    unit="m",
                    quantity=100.0,
                )
            ],
            goal_statement="Cover the BOM",
            approver_email="approver@sim.local",
            escalation_subject_protocol="[REF:<supplier_id>]",
        ),
        directory=directory
        or [
            SupplierEntry(
                supplier_id="p01",
                email="p01@sim.local",
                material_ids=["STL-BEAM-200"],
            )
        ],
        price_history=price_history
        or [
            PriceHistoryRow(
                supplier_id="p01",
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=100.0,
            )
        ],
        clock=_clock(),
    )


def _quote_line(
    *,
    material_id: str | None = "STL-BEAM-200",
    quantity: float = 100.0,
    unit_price: float = 100.0,
    total: float | None = None,
) -> QuoteLine:
    resolved_total = total if total is not None else quantity * unit_price
    return QuoteLine(
        material_id=material_id,
        description="Steel I-Beam 200mm",
        quantity=quantity,
        unit_price=unit_price,
        total=resolved_total,
    )


def _as_sent(
    *,
    line_items: list[QuoteLine] | None = None,
    payment_terms: str = "Net 30",
    validity_days: int = 14,
    grand_total: float | None = None,
) -> AsSentQuote:
    items = [_quote_line()] if line_items is None else line_items
    resolved_grand_total = (
        grand_total if grand_total is not None else sum(line.total for line in items)
    )
    return AsSentQuote(
        line_items=items,
        payment_terms=payment_terms,
        validity_days=validity_days,
        grand_total=resolved_grand_total,
    )


def _quote_record(
    *,
    as_sent: AsSentQuote | None = None,
    revised_as_sent: AsSentQuote | None = None,
) -> QuoteRecord:
    document = _as_sent() if as_sent is None else as_sent
    recomputed_total = 0.0 if not document.line_items else document.line_items[0].total
    return QuoteRecord(
        as_sent=document,
        recomputed_total=recomputed_total,
        recomputed_grand_total=document.grand_total,
        revised_as_sent=revised_as_sent,
    )


@pytest.mark.unit
def test_required_classes_includes_class_1_when_catalog_line_missing_from_quote() -> None:
    rfq = _rfq()
    quote = _quote_record(
        as_sent=_as_sent(
            line_items=[
                QuoteLine(
                    material_id="CU-WIRE-10",
                    description="Copper Wire 10AWG",
                    quantity=1.0,
                    unit_price=1.0,
                    total=1.0,
                )
            ]
        )
    )

    assert required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=False,
        own_quote_history=[],
    ) == frozenset({1})


@pytest.mark.unit
def test_required_classes_omits_classes_1_3_4_when_quote_has_no_line_items() -> None:
    rfq = _rfq()
    quote = _quote_record(as_sent=_as_sent(line_items=[], payment_terms="", validity_days=0))

    assert (
        required_classes(
            quote,
            rfq,
            supplier_id="p01",
            injection_suspected=False,
            own_quote_history=[],
        )
        == frozenset()
    )


@pytest.mark.unit
def test_required_classes_includes_class_7_when_empty_quote_is_injection() -> None:
    rfq = _rfq()
    quote = _quote_record(as_sent=_as_sent(line_items=[], payment_terms="", validity_days=0))

    assert required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=True,
        own_quote_history=[],
    ) == frozenset({7})


@pytest.mark.unit
def test_required_classes_omits_class_1_when_missing_line_not_in_supplier_catalog() -> None:
    rfq = _rfq(
        directory=[
            SupplierEntry(
                supplier_id="p01",
                email="p01@sim.local",
                material_ids=["OTHER-MAT"],
            )
        ]
    )
    quote = _quote_record(as_sent=_as_sent(line_items=[]))

    assert (
        required_classes(
            quote,
            rfq,
            supplier_id="p01",
            injection_suspected=False,
            own_quote_history=[],
        )
        == frozenset()
    )


@pytest.mark.unit
def test_required_classes_omits_class_1_when_quote_has_extra_uncatalogued_line() -> None:
    rfq = _rfq()
    quote = _quote_record(
        as_sent=_as_sent(
            line_items=[
                _quote_line(),
                QuoteLine(
                    material_id="EXTRA-MAT",
                    description="Extra material",
                    quantity=1.0,
                    unit_price=1.0,
                    total=1.0,
                ),
            ]
        )
    )

    assert (
        required_classes(
            quote,
            rfq,
            supplier_id="p01",
            injection_suspected=False,
            own_quote_history=[],
        )
        == frozenset()
    )


@pytest.mark.unit
def test_required_classes_includes_class_2_when_quantity_differs_from_bom() -> None:
    rfq = _rfq()
    quote = _quote_record(as_sent=_as_sent(line_items=[_quote_line(quantity=90.0)]))

    assert required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=False,
        own_quote_history=[],
    ) == frozenset({2})


@pytest.mark.unit
def test_required_classes_includes_class_3_when_payment_terms_differ() -> None:
    rfq = _rfq()
    quote = _quote_record(as_sent=_as_sent(payment_terms="Net 60"))

    assert required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=False,
        own_quote_history=[],
    ) == frozenset({3})


@pytest.mark.unit
@pytest.mark.parametrize(
    ("validity_days", "expected"),
    [
        (14, frozenset()),
        (13, frozenset({4})),
    ],
)
def test_required_classes_validity_boundary(
    validity_days: int,
    expected: frozenset[int],
) -> None:
    rfq = _rfq(required_validity_days=14)
    quote = _quote_record(as_sent=_as_sent(validity_days=validity_days))

    assert (
        required_classes(
            quote,
            rfq,
            supplier_id="p01",
            injection_suspected=False,
            own_quote_history=[],
        )
        == expected
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("unit_price", "expected"),
    [
        (105.0, frozenset()),
        (105.01, frozenset({5})),
    ],
)
def test_required_classes_price_ceiling_boundary(
    unit_price: float,
    expected: frozenset[int],
) -> None:
    rfq = _rfq(target_price_ceiling_pct=5.0)
    quote = _quote_record(as_sent=_as_sent(line_items=[_quote_line(unit_price=unit_price)]))

    assert (
        required_classes(
            quote,
            rfq,
            supplier_id="p01",
            injection_suspected=False,
            own_quote_history=[],
        )
        == expected
    )


@pytest.mark.unit
def test_required_classes_uses_supplier_specific_price_history_for_class_5() -> None:
    rfq = _rfq(
        price_history=[
            PriceHistoryRow(
                supplier_id="p01",
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=100.0,
            ),
            PriceHistoryRow(
                supplier_id="p02",
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=200.0,
            ),
        ]
    )
    quote = _quote_record(as_sent=_as_sent(line_items=[_quote_line(unit_price=110.0)]))

    assert required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=False,
        own_quote_history=[],
    ) == frozenset({5})


@pytest.mark.unit
def test_required_classes_includes_class_6_when_own_quote_history_non_empty() -> None:
    rfq = _rfq()
    quote = _quote_record()
    history = [_as_sent()]

    assert required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=False,
        own_quote_history=history,
    ) == frozenset({6})


@pytest.mark.unit
def test_required_classes_omits_class_6_when_own_quote_history_empty() -> None:
    rfq = _rfq()
    quote = _quote_record()

    assert (
        required_classes(
            quote,
            rfq,
            supplier_id="p01",
            injection_suspected=False,
            own_quote_history=[],
        )
        == frozenset()
    )


@pytest.mark.unit
@pytest.mark.parametrize("injection_suspected", [True, False])
def test_required_classes_class_7_follows_injection_suspected_only(
    injection_suspected: bool,
) -> None:
    rfq = _rfq()
    quote = _quote_record()

    result = required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=injection_suspected,
        own_quote_history=[],
    )

    if injection_suspected:
        assert result == frozenset({7})
    else:
        assert 7 not in result


@pytest.mark.unit
def test_required_classes_includes_class_7_with_other_classes_when_injection_suspected() -> None:
    rfq = _rfq()
    quote = _quote_record(as_sent=_as_sent(payment_terms="Net 60"))

    assert required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=True,
        own_quote_history=[],
    ) == frozenset({3, 7})


@pytest.mark.unit
def test_required_classes_omits_classes_for_arithmetic_errors_only() -> None:
    rfq = _rfq()
    quote = _quote_record(
        as_sent=_as_sent(
            line_items=[_quote_line(total=999.0)],
            grand_total=999.0,
        )
    )

    assert (
        required_classes(
            quote,
            rfq,
            supplier_id="p01",
            injection_suspected=False,
            own_quote_history=[],
        )
        == frozenset()
    )


@pytest.mark.unit
def test_required_classes_uses_revised_as_sent_when_present() -> None:
    rfq = _rfq()
    quote = _quote_record(
        as_sent=_as_sent(payment_terms="Net 60"),
        revised_as_sent=_as_sent(payment_terms="Net 30"),
    )

    assert (
        required_classes(
            quote,
            rfq,
            supplier_id="p01",
            injection_suspected=False,
            own_quote_history=[],
        )
        == frozenset()
    )


@pytest.mark.unit
def test_required_classes_omits_class_2_when_quote_line_has_no_material_id() -> None:
    rfq = _rfq()
    quote = _quote_record(
        as_sent=_as_sent(line_items=[_quote_line(material_id=None, quantity=90.0)])
    )

    assert required_classes(
        quote,
        rfq,
        supplier_id="p01",
        injection_suspected=False,
        own_quote_history=[],
    ) == frozenset({1})
