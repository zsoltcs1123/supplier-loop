import pytest

from supplier_loop.extract.schema import ExtractResult
from supplier_loop.quote_pipeline.pipeline import build_quote_record
from supplier_loop.quote_pipeline.recompute import recomputed_grand_total, recomputed_line_total
from supplier_loop.round_state.models import QuoteLine, RfqContext
from supplier_loop.simulator.port import Assignment, BomLine, SimClock


def _rfq() -> RfqContext:
    return RfqContext(
        assignment=Assignment(
            rfq_id="RFQ-001",
            required_payment_terms="Net 30",
            required_validity_days=14,
            target_price_ceiling_pct=5.0,
            line_items=[
                BomLine(
                    material_id="STL-BEAM-200",
                    description="Steel I-Beam 200mm",
                    unit="m",
                    quantity=100.0,
                ),
                BomLine(
                    material_id="CU-WIRE-10",
                    description="Copper Wire 10AWG",
                    unit="m",
                    quantity=40.0,
                ),
            ],
            goal_statement="Cover the BOM",
            approver_email="approver@sim.local",
            escalation_subject_protocol="[REF:<supplier_id>]",
        ),
        directory=[],
        price_history=[],
        clock=SimClock(
            sim_time_seconds=0.0,
            sim_time_days=0.0,
            round_id="dev-1",
            mode="development",
            clock_factor=60.0,
        ),
    )


@pytest.mark.unit
def test_recomputed_line_total_uses_qty_times_unit_price_when_printed_total_wrong() -> None:
    assert recomputed_line_total(50.0, 42.29) == 2114.5


@pytest.mark.unit
def test_recomputed_grand_total_sums_line_totals_when_printed_grand_total_wrong() -> None:
    assert recomputed_grand_total([2114.5, 123.2]) == 2237.7


@pytest.mark.unit
def test_build_quote_record_keeps_as_sent_totals_when_arithmetic_is_wrong() -> None:
    extracted = ExtractResult(
        line_items=[
            QuoteLine(
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                quantity=50.0,
                unit_price=42.29,
                total=1.0,
            ),
            QuoteLine(
                material_id=None,
                description="Copper Wire 10AWG",
                quantity=40.0,
                unit_price=3.08,
                total=9.0,
            ),
        ],
        payment_terms="Net 30",
        validity_days=30,
        grand_total=99.0,
        injection_suspected=False,
    )

    record = build_quote_record(extracted, _rfq())

    assert record.as_sent.grand_total == 99.0
    assert [line.total for line in record.as_sent.line_items] == [1.0, 9.0]
    assert [line.quantity for line in record.as_sent.line_items] == [50.0, 40.0]
    assert [line.unit_price for line in record.as_sent.line_items] == [42.29, 3.08]
    assert record.as_sent.payment_terms == "Net 30"
    assert record.as_sent.validity_days == 30
    assert record.recomputed_total == 2237.7
    assert record.recomputed_grand_total == 2237.7
    assert record.revised_as_sent is None


@pytest.mark.unit
def test_build_quote_record_fills_material_id_when_description_matches_bom() -> None:
    extracted = ExtractResult(
        line_items=[
            QuoteLine(
                material_id=None,
                description="Steel I-Beam 200mm (STL-BEAM-200)",
                quantity=50.0,
                unit_price=42.29,
                total=2114.5,
            )
        ],
        payment_terms="Net 30",
        validity_days=30,
        grand_total=2114.5,
        injection_suspected=False,
    )

    record = build_quote_record(extracted, _rfq())

    assert record.as_sent.line_items[0].material_id == "STL-BEAM-200"


@pytest.mark.unit
def test_build_quote_record_leaves_material_id_empty_when_description_unknown() -> None:
    extracted = ExtractResult(
        line_items=[
            QuoteLine(
                material_id=None,
                description="Unobtainium Rod",
                quantity=1.0,
                unit_price=10.0,
                total=10.0,
            )
        ],
        payment_terms="Net 30",
        validity_days=14,
        grand_total=10.0,
        injection_suspected=False,
    )

    record = build_quote_record(extracted, _rfq())

    assert record.as_sent.line_items[0].material_id is None


@pytest.mark.unit
def test_build_quote_record_does_not_invent_lines_when_extract_omits_bom_items() -> None:
    extracted = ExtractResult(
        line_items=[
            QuoteLine(
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                quantity=50.0,
                unit_price=42.29,
                total=2114.5,
            )
        ],
        payment_terms="Net 30",
        validity_days=30,
        grand_total=2114.5,
        injection_suspected=False,
    )

    record = build_quote_record(extracted, _rfq())

    assert [line.material_id for line in record.as_sent.line_items] == ["STL-BEAM-200"]
