from datetime import UTC, datetime
from pathlib import Path

import pytest

from supplier_loop.extract.fixture import FixtureExtractor
from supplier_loop.extract.schema import ExtractResult
from supplier_loop.operational_log.log import LogEvent, OperationalLog
from supplier_loop.orchestrator.run import run_pass, run_until_submit
from supplier_loop.round_state.models import QuoteLine
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


def _quote_body() -> str:
    return (
        "Quote for your RFQ\n"
        "qty 100 Steel I-Beam 200mm 40.00 USD\n"
        "qty 50 Aluminum Plate 10mm 25.00 USD\n"
        "Payment Net 30, validity 14 days"
    )


def _simulator(round_id: str) -> InMemorySimulator:
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
        history=[
            PriceHistoryRow(
                supplier_id="p01",
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=40.0,
            ),
            PriceHistoryRow(
                supplier_id="p02",
                material_id="ALU-PLATE-10",
                description="Aluminum Plate 10mm",
                unit="sheet",
                last_accepted_unit_price=25.0,
            ),
        ],
        clock=SimClock(
            sim_time_seconds=3600.0,
            sim_time_days=0.042,
            round_id=round_id,
            mode="development",
            clock_factor=60.0,
        ),
        inbox=[],
        attachments={},
    )


def _extract_result_p01() -> ExtractResult:
    return ExtractResult(
        line_items=[
            QuoteLine(
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                quantity=100.0,
                unit_price=40.0,
                total=4000.0,
            )
        ],
        payment_terms="Net 30",
        validity_days=14,
        grand_total=4000.0,
        injection_suspected=False,
    )


def _extract_result_p02() -> ExtractResult:
    return ExtractResult(
        line_items=[
            QuoteLine(
                material_id="ALU-PLATE-10",
                description="Aluminum Plate 10mm",
                quantity=50.0,
                unit_price=25.0,
                total=1250.0,
            )
        ],
        payment_terms="Net 30",
        validity_days=14,
        grand_total=1250.0,
        injection_suspected=False,
    )


def _push_quotes(simulator: InMemorySimulator) -> FixtureExtractor:
    simulator.push_inbox(
        InboxEntry(
            id="in-p01",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.0,
            attachment_ids=[],
        ),
        body=_quote_body(),
    )
    simulator.push_inbox(
        InboxEntry(
            id="in-p02",
            from_address="p02@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.5,
            attachment_ids=[],
        ),
        body=_quote_body(),
    )
    return FixtureExtractor(
        {
            "in-p01": _extract_result_p01(),
            "in-p02": _extract_result_p02(),
        }
    )


@pytest.mark.integration
def test_orchestrator_submits_clean_quotes_when_all_relevant_suppliers_reply(
    tmp_path: Path,
) -> None:
    round_root = tmp_path / "round"
    log_path = tmp_path / "logs" / "operational.jsonl"
    store = RoundStore(round_root)
    log = OperationalLog(log_path)
    simulator = _simulator("dev-1")
    snapshot_world(simulator, store)

    assert run_pass(simulator, store, FixtureExtractor({}), log) is False
    saved = store.load()
    assert saved.suppliers["p01"].phase == "rfq_sent"
    assert saved.suppliers["p02"].phase == "rfq_sent"

    rfq_recipients = {mail.to for mail in simulator.sent_emails()}
    assert rfq_recipients == {"p01@sim.local", "p02@sim.local"}
    assert len(simulator.sent_emails()) == 2

    extractor = _push_quotes(simulator)
    submission = run_until_submit(simulator, store, extractor, log)

    rfq_after = [mail for mail in simulator.sent_emails() if mail.to != "approver@sim.local"]
    assert {mail.to for mail in rfq_after} == {"p01@sim.local", "p02@sim.local"}
    assert len(rfq_after) == 2
    assert set(submission) == {"p01", "p02"}
    for supplier_id in ("p01", "p02"):
        entry = submission[supplier_id]
        assert entry.action_taken == "extract"
        assert entry.auto_approved is True

    saved = store.load()
    raw = (round_root / "round.json").read_text(encoding="utf-8")
    assert "action_taken" not in raw
    assert "auto_approved" not in raw
    assert saved.suppliers["p01"].quote is not None
    assert saved.suppliers["p02"].quote is not None
    assert saved.suppliers["p01"].phase == "done"
    assert saved.suppliers["p02"].phase == "done"
    submit_events = [event for event in log.events_for_round("dev-1") if event.kind == "submit"]
    assert submit_events
    assert submit_events[-1].detail["warnings"] == []


@pytest.mark.integration
def test_orchestrator_wipes_quotes_but_keeps_log_when_new_round_starts(
    tmp_path: Path,
) -> None:
    round_root = tmp_path / "round"
    log_path = tmp_path / "logs" / "operational.jsonl"
    store = RoundStore(round_root)
    log = OperationalLog(log_path)
    simulator = _simulator("dev-1")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)
    submission = run_until_submit(simulator, store, _push_quotes(simulator), log)
    assert submission is not None

    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 12, 0, tzinfo=UTC),
            sim_time_seconds=7200.0,
            round_id="dev-1",
            kind="round_marker",
            detail={"round_id": "dev-1"},
        )
    )
    first_log_lines = log_path.read_text(encoding="utf-8").splitlines()
    assert any("dev-1" in line and "round_marker" in line for line in first_log_lines)

    store.wipe()
    simulator = _simulator("dev-2")
    snapshot_world(simulator, store)
    reloaded = store.load()

    assert reloaded.rfq.clock.round_id == "dev-2"
    assert all(facts.quote is None for facts in reloaded.suppliers.values())
    assert len(log_path.read_text(encoding="utf-8").splitlines()) >= len(first_log_lines)
