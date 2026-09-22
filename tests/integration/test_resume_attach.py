from pathlib import Path

import pytest

from supplier_loop.round_state.store import RoundStore, snapshot_world, stored_round_id
from supplier_loop.simulator.memory import InMemorySimulator
from supplier_loop.simulator.port import (
    Assignment,
    BomLine,
    InboxEntry,
    SimClock,
    SupplierEntry,
)


def _simulator(round_id: str, inbox_ids: list[str]) -> InMemorySimulator:
    return InMemorySimulator(
        assignment=Assignment(
            rfq_id=f"RFQ-{round_id}",
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
        history=[],
        clock=SimClock(
            sim_time_seconds=1000.0,
            sim_time_days=0.01,
            round_id=round_id,
            mode="exam",
            clock_factor=60.0,
        ),
        inbox=[
            InboxEntry(
                id=email_id,
                from_address="p01@sim.local",
                to_address="buyer@sim.local",
                subject=f"Subject for {email_id}",
                sim_time_hours=1.0,
                attachment_ids=[],
            )
            for email_id in inbox_ids
        ],
        attachments={},
    )


@pytest.mark.integration
def test_stored_round_id_is_none_when_round_file_missing(tmp_path: Path) -> None:
    store = RoundStore(tmp_path)

    assert stored_round_id(store) is None


@pytest.mark.integration
def test_resume_attach_wipes_and_snapshots_when_round_id_differs(tmp_path: Path) -> None:
    store = RoundStore(tmp_path)
    snapshot_world(_simulator("dev-1", []), store)
    state = store.load()
    state.suppliers["p01"].phase = "escalated"
    store.save(state)
    (tmp_path / "sent.json").write_text(
        '[{"id":"sent-1","to":"p01@sim.local","subject":"RFQ","body":"please quote"}]',
        encoding="utf-8",
    )

    new_sim = _simulator("exam-1", ["in-exam"])
    assert stored_round_id(store) != new_sim.get_sim_clock().round_id

    store.wipe()
    snapshot_world(new_sim, store)

    reloaded = store.load()
    assert reloaded.rfq.clock.round_id == "exam-1"
    assert reloaded.rfq.assignment.rfq_id == "RFQ-exam-1"
    assert reloaded.suppliers["p01"].phase == "idle"
    assert [entry.id for entry in reloaded.inbox] == ["in-exam"]
    assert not (tmp_path / "sent.json").exists()


@pytest.mark.integration
def test_resume_attach_keeps_state_when_round_id_matches(tmp_path: Path) -> None:
    store = RoundStore(tmp_path)
    simulator = _simulator("dev-1", [])
    snapshot_world(simulator, store)
    state = store.load()
    state.suppliers["p01"].phase = "quoted"
    store.save(state)
    sent_path = tmp_path / "sent.json"
    sent_path.write_text(
        '[{"id":"sent-1","to":"p01@sim.local","subject":"RFQ","body":"please quote"}]',
        encoding="utf-8",
    )

    assert stored_round_id(store) == simulator.get_sim_clock().round_id

    reloaded = store.load()
    assert reloaded.suppliers["p01"].phase == "quoted"
    assert sent_path.exists()


@pytest.mark.integration
def test_resume_attach_snapshots_when_round_file_missing(tmp_path: Path) -> None:
    store = RoundStore(tmp_path)
    simulator = _simulator("exam-1", [])

    snapshot_world(simulator, store)

    assert stored_round_id(store) == "exam-1"
    assert store.load().suppliers["p01"].phase == "idle"
