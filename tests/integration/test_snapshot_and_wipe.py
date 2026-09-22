import io
from datetime import UTC, datetime
from pathlib import Path

import pytest

from supplier_loop.operational_log.log import LogEvent, OperationalLog
from supplier_loop.progress import emit_progress
from supplier_loop.round_state.store import RoundStore, snapshot_world
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
        history=[],
        clock=SimClock(
            sim_time_seconds=1000.0,
            sim_time_days=0.01,
            round_id=round_id,
            mode="development",
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
def test_snapshot_and_wipe_preserves_log_when_round_state_cleared(
    tmp_path: Path,
) -> None:
    round_root = tmp_path / "round"
    log_path = tmp_path / "logs" / "operational.jsonl"
    store = RoundStore(round_root)
    log = OperationalLog(log_path)

    snapshot_world(_simulator("dev-1", ["in-round-1"]), store)
    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 9, 0, tzinfo=UTC),
            sim_time_seconds=10.0,
            round_id="dev-1",
            kind="ingest",
            detail={"email_id": "in-round-1"},
        )
    )
    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 9, 1, tzinfo=UTC),
            sim_time_seconds=20.0,
            round_id="dev-1",
            kind="decision",
            detail={"note": "watermark \u2014 kept"},
        )
    )
    (round_root / "sent.json").write_text("[]", encoding="utf-8")

    store.wipe()

    assert not (round_root / "round.json").exists()
    assert not (round_root / "sent.json").exists()
    with pytest.raises(FileNotFoundError):
        store.load()

    log_lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 2

    snapshot_world(_simulator("dev-2", ["in-round-2"]), store)
    reloaded = store.load()

    assert reloaded.rfq.clock.round_id == "dev-2"
    assert [entry.id for entry in reloaded.inbox] == ["in-round-2"]
    assert all(facts.quote is None for facts in reloaded.suppliers.values())
    assert len(log_path.read_text(encoding="utf-8").splitlines()) >= 2


@pytest.mark.integration
def test_snapshot_and_wipe_progress_stays_separate_from_log(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "logs" / "operational.jsonl"
    log = OperationalLog(log_path)
    stream = io.StringIO()

    emit_progress(
        stream,
        sim_time_seconds=500.0,
        kind="reminder_due",
        subject="p02 reminder_due",
        wall_time=datetime(2026, 9, 21, 16, 9, 12),
    )
    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 10, 0, tzinfo=UTC),
            sim_time_seconds=500.0,
            round_id="dev-1",
            kind="reminder_due",
            detail={"supplier_id": "p02"},
        )
    )

    assert stream.getvalue() == "16:09:12  8m 20s  reminder_due  p02 reminder_due\n"
    assert not stream.getvalue().startswith("{")
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 1
