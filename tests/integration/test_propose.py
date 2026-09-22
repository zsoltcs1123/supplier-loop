from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pytest

from supplier_loop.cli import main
from supplier_loop.extract.spend import load_spend, record_spend
from supplier_loop.operational_log.log import LogEvent, OperationalLog
from supplier_loop.propose import write_pack
from supplier_loop.round_state.store import RoundStore, snapshot_world
from supplier_loop.simulator.memory import InMemorySimulator
from supplier_loop.simulator.port import (
    Assignment,
    BomLine,
    PriceHistoryRow,
    SimClock,
    SupplierEntry,
)


def _simulator() -> InMemorySimulator:
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
            round_id="dev-1",
            mode="development",
            clock_factor=60.0,
        ),
        inbox=[],
        attachments={},
    )


def _finished_round(tmp_path: Path) -> None:
    store = RoundStore(tmp_path / "round")
    snapshot_world(_simulator(), store)
    state = store.load()
    state.suppliers["p01"].phase = "done"
    state.suppliers["p02"].phase = "quoted"
    store.save(state)
    log = OperationalLog(tmp_path / "ops.jsonl")
    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 12, 0, tzinfo=UTC),
            sim_time_seconds=7200.0,
            round_id="dev-1",
            kind="submit",
            detail={"suppliers": ["p01", "p02"], "warnings": ["missing field"]},
        )
    )
    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 12, 1, tzinfo=UTC),
            sim_time_seconds=7300.0,
            round_id="dev-2",
            kind="ingest",
            detail={"email_id": "other-round"},
        )
    )


@pytest.mark.integration
def test_pack_propose_writes_pack_from_disk_without_changing_spend(tmp_path: Path) -> None:
    _finished_round(tmp_path)
    spend_path = tmp_path / "llm-spend.json"
    record_spend(
        model="google/gemini-2.5-pro",
        cost=0.21,
        prompt_tokens=10,
        completion_tokens=4,
        path=spend_path,
        wall_time=datetime(2026, 9, 21, 12, 0, tzinfo=UTC),
    )
    used_before = load_spend(spend_path).used
    out = StringIO()

    path = write_pack(artifacts_root=tmp_path, out=out)

    text = path.read_text(encoding="utf-8")
    assert path == tmp_path / "proposals" / "dev-1" / "pack.md"
    assert "round_id: dev-1" in text
    assert "- p01: done" in text
    assert "- p02: quoted" in text
    assert "- reminder" in text
    assert "- quiet margin" in text
    assert "- settle wait" in text
    assert "- negotiation wait" in text
    assert "- SOP wording" in text
    assert "- Never list" in text
    assert "missing field" in text
    assert "other-round" not in text
    assert load_spend(spend_path).used == used_before
    assert used_before == 0.21
    assert out.getvalue() == f"{path}\n"


@pytest.mark.integration
def test_pack_propose_exits_when_round_state_missing(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="No round state"):
        write_pack(artifacts_root=tmp_path)


@pytest.mark.integration
def test_main_pack_propose_runs_without_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SUPPLIER_SIM_MCP_URL", raising=False)
    monkeypatch.delenv("SUPPLIER_SIM_TOKEN", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _finished_round(tmp_path / ".artifacts")

    main(["pack-propose"])

    pack = tmp_path / ".artifacts" / "proposals" / "dev-1" / "pack.md"
    assert pack.is_file()
    text = pack.read_text(encoding="utf-8")
    assert "round_id: dev-1" in text
    assert "- p01: done" in text
