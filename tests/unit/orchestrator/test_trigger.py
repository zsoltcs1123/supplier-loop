import pytest

from supplier_loop.orchestrator.trigger import should_run_pass
from supplier_loop.round_state.models import (
    AsSentQuote,
    DedupRegistry,
    QuoteRecord,
    RfqContext,
    RoundState,
    SupplierFacts,
    SupplierPhase,
)
from supplier_loop.simulator.port import (
    Assignment,
    BomLine,
    InboxEntry,
    SimClock,
    SupplierEntry,
)


def _state(
    *,
    phases: dict[str, SupplierPhase] | None = None,
    inbox_ids: list[str] | None = None,
    seen_ids: set[str] | None = None,
) -> RoundState:
    phases = phases or {}
    inbox_ids = inbox_ids or []
    seen_ids = seen_ids or set()
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
                    ),
                    BomLine(
                        material_id="ALU-PLATE-10",
                        description="Aluminum Plate 10mm",
                        unit="sheet",
                        quantity=50.0,
                    ),
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
                ),
                SupplierEntry(
                    supplier_id="p02",
                    email="p02@sim.local",
                    material_ids=["ALU-PLATE-10"],
                ),
                SupplierEntry(
                    supplier_id="p03",
                    email="p03@sim.local",
                    material_ids=["WOOD-PLANK"],
                ),
            ],
            price_history=[],
            clock=SimClock(
                sim_time_seconds=100.0,
                sim_time_days=0.01,
                round_id="dev-1",
                mode="development",
                clock_factor=60.0,
            ),
        ),
        suppliers={
            "p01": SupplierFacts(
                supplier_id="p01",
                email="p01@sim.local",
                phase=phases.get("p01", "idle"),
            ),
            "p02": SupplierFacts(
                supplier_id="p02",
                email="p02@sim.local",
                phase=phases.get("p02", "idle"),
            ),
            "p03": SupplierFacts(
                supplier_id="p03",
                email="p03@sim.local",
                phase=phases.get("p03", "idle"),
            ),
        },
        inbox=[
            InboxEntry(
                id=email_id,
                from_address="p01@sim.local",
                to_address="buyer@sim.local",
                subject="Quote",
                sim_time_hours=1.0,
                attachment_ids=[],
            )
            for email_id in inbox_ids
        ],
        dedup=DedupRegistry(email_ids=seen_ids),
    )


@pytest.mark.unit
def test_trigger_runs_pass_when_idle_relevant_supplier_exists() -> None:
    assert should_run_pass(_state()) is True


@pytest.mark.unit
def test_trigger_runs_pass_when_inbox_delta_exists() -> None:
    assert should_run_pass(_state(inbox_ids=["in-1"], seen_ids=set())) is True


@pytest.mark.unit
def test_trigger_skips_pass_when_no_delta_and_no_idle_relevant() -> None:
    state = _state(
        phases={"p01": "awaiting_quote", "p02": "awaiting_quote"},
        inbox_ids=["in-1"],
        seen_ids={"in-1"},
    )

    assert should_run_pass(state) is False


@pytest.mark.unit
def test_trigger_runs_pass_when_quote_has_no_line_items() -> None:
    state = _state(
        phases={"p01": "quoted", "p02": "awaiting_quote"},
        inbox_ids=["in-1"],
        seen_ids={"in-1"},
    )
    state.suppliers["p01"].quote = QuoteRecord(
        as_sent=AsSentQuote(
            line_items=[],
            payment_terms="Net 30",
            validity_days=30,
            grand_total=0.0,
        ),
        recomputed_total=0.0,
        recomputed_grand_total=0.0,
    )

    assert should_run_pass(state) is True
