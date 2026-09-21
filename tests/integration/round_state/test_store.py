from pathlib import Path

import pytest

from supplier_loop.round_state.models import (
    AsSentQuote,
    QuoteLine,
    QuoteRecord,
)
from supplier_loop.round_state.store import RoundStore, snapshot_world
from supplier_loop.simulator.memory import InMemorySimulator
from supplier_loop.simulator.port import (
    Assignment,
    BomLine,
    InboxEntry,
    PriceHistoryRow,
    SimClock,
    SupplierEntry,
)


def _simulator(
    round_id: str,
    inbox: list[InboxEntry] | None = None,
) -> InMemorySimulator:
    return InMemorySimulator(
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
            ),
            SupplierEntry(
                supplier_id="p02",
                email="p02@sim.local",
                material_ids=["STL-BEAM-200"],
            ),
        ],
        history=[
            PriceHistoryRow(
                supplier_id="p01",
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=42.0,
            )
        ],
        clock=SimClock(
            sim_time_seconds=3600.0,
            sim_time_days=0.042,
            round_id=round_id,
            mode="development",
            clock_factor=60.0,
        ),
        inbox=inbox
        or [
            InboxEntry(
                id="in-1",
                from_address="p01@sim.local",
                to_address="buyer@sim.local",
                subject="Quote",
                sim_time_hours=1.0,
                attachment_ids=["att-1"],
            )
        ],
        attachments={},
    )


@pytest.mark.integration
def test_store_snapshot_persists_world_when_saved(tmp_path: Path) -> None:
    root = tmp_path / "round"
    root.mkdir()
    store = RoundStore(root)
    simulator = _simulator("dev-1")

    snapshot_world(simulator, store)
    loaded = store.load()

    assert loaded.rfq.assignment.rfq_id == "RFQ-001"
    assert len(loaded.rfq.directory) == 2
    assert loaded.rfq.price_history[0].supplier_id == "p01"
    assert loaded.rfq.clock.round_id == "dev-1"
    assert [entry.id for entry in loaded.inbox] == ["in-1"]
    assert set(loaded.suppliers) == {"p01", "p02"}
    assert all(facts.phase == "idle" for facts in loaded.suppliers.values())
    assert all(facts.quote is None for facts in loaded.suppliers.values())
    assert loaded.dedup.email_ids == set()


@pytest.mark.integration
def test_store_save_roundtrips_quote_and_dedup_when_loaded(tmp_path: Path) -> None:
    store = RoundStore(tmp_path / "round")
    state = snapshot_world(_simulator("dev-1"), store)
    state.suppliers["p01"].quote = QuoteRecord(
        as_sent=AsSentQuote(
            line_items=[
                QuoteLine(
                    material_id=None,
                    description="Steel I-Beam 200mm",
                    quantity=100.0,
                    unit_price=40.0,
                    total=4000.0,
                )
            ],
            payment_terms="Net 30",
            validity_days=14,
            grand_total=4000.0,
        ),
        recomputed_total=4000.0,
        recomputed_grand_total=4000.0,
    )
    state.dedup.email_ids.add("in-1")
    state.dedup.attachment_ids.add("att-1")
    state.dedup.quote_fingerprints.add("fp-1")
    store.save(state)

    loaded = store.load()
    quote = loaded.suppliers["p01"].quote

    assert quote is not None
    assert quote.as_sent.line_items[0].material_id is None
    assert quote.as_sent.line_items[0].description == "Steel I-Beam 200mm"
    assert quote.recomputed_grand_total == 4000.0
    assert loaded.dedup.email_ids == {"in-1"}
    assert loaded.dedup.attachment_ids == {"att-1"}
    assert loaded.dedup.quote_fingerprints == {"fp-1"}
    assert loaded.suppliers["p02"].quote is None
