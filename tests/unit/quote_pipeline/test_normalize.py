import pytest

from supplier_loop.quote_pipeline.normalize import (
    canonical_description,
    description_catalog,
    normalize_quote_line,
)
from supplier_loop.round_state.models import QuoteLine, RfqContext
from supplier_loop.simulator.port import Assignment, BomLine, PriceHistoryRow, SimClock


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
                )
            ],
            goal_statement="Cover the BOM",
            approver_email="approver@sim.local",
            escalation_subject_protocol="[REF:<supplier_id>]",
        ),
        directory=[],
        price_history=[
            PriceHistoryRow(
                supplier_id="p01",
                material_id="OTHER-ID",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=40.0,
            )
        ],
        clock=SimClock(
            sim_time_seconds=0.0,
            sim_time_days=0.0,
            round_id="dev-1",
            mode="development",
            clock_factor=60.0,
        ),
    )


@pytest.mark.unit
def test_canonical_description_strips_trailing_sku_when_present() -> None:
    assert canonical_description("Steel I-Beam 200mm (STL-BEAM-200)") == "steel i-beam 200mm"


@pytest.mark.unit
def test_normalize_quote_line_keeps_extracted_material_id_when_present() -> None:
    line = QuoteLine(
        material_id="KEEP-ME",
        description="Steel I-Beam 200mm",
        quantity=1.0,
        unit_price=1.0,
        total=1.0,
    )

    normalized = normalize_quote_line(line, {"steel i-beam 200mm": "STL-BEAM-200"})

    assert normalized.material_id == "KEEP-ME"


@pytest.mark.unit
def test_description_catalog_omits_description_when_material_ids_conflict() -> None:
    catalog = description_catalog(_rfq())

    assert "steel i-beam 200mm" not in catalog
