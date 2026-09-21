import pytest
from pydantic import ValidationError

from supplier_loop.round_state.models import (
    DedupRegistry,
    RfqContext,
    RoundState,
    SupplierFacts,
)
from supplier_loop.simulator.port import (
    Assignment,
    BomLine,
    SimClock,
    SupplierEntry,
)


def _minimal_round_state() -> RoundState:
    return RoundState(
        rfq=RfqContext(
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
            directory=[
                SupplierEntry(
                    supplier_id="p01",
                    email="p01@sim.local",
                    material_ids=["STL-BEAM-200"],
                )
            ],
            price_history=[],
            clock=SimClock(
                sim_time_seconds=0.0,
                sim_time_days=0.0,
                round_id="dev-1",
                mode="development",
                clock_factor=60.0,
            ),
        ),
        suppliers={
            "p01": SupplierFacts(supplier_id="p01", email="p01@sim.local"),
        },
        inbox=[],
        dedup=DedupRegistry(),
    )


@pytest.mark.unit
def test_models_round_state_rejects_action_taken_when_extra_field() -> None:
    state = _minimal_round_state()

    with pytest.raises(ValidationError, match="action_taken"):
        RoundState(**{**state.model_dump(), "action_taken": "extract"})


@pytest.mark.unit
def test_models_round_state_rejects_auto_approved_when_extra_field() -> None:
    state = _minimal_round_state()

    with pytest.raises(ValidationError, match="auto_approved"):
        RoundState(**{**state.model_dump(), "auto_approved": True})
