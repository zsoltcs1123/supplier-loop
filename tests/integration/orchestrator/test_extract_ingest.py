from pathlib import Path

import pytest

from supplier_loop.extract.fixture import FixtureExtractor
from supplier_loop.extract.schema import ExtractResult
from supplier_loop.operational_log.log import OperationalLog
from supplier_loop.orchestrator.run import run_pass
from supplier_loop.round_state.models import QuoteLine
from supplier_loop.round_state.store import RoundStore, snapshot_world
from supplier_loop.simulator.memory import InMemorySimulator
from supplier_loop.simulator.port import (
    Assignment,
    Attachment,
    BomLine,
    InboxEntry,
    PriceHistoryRow,
    SimClock,
    SupplierEntry,
)


def _simulator(*, attachments: dict[str, Attachment] | None = None) -> InMemorySimulator:
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
        history=[
            PriceHistoryRow(
                supplier_id="p01",
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=40.0,
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
        attachments=attachments or {},
    )


def _quoted() -> ExtractResult:
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


def _empty() -> ExtractResult:
    return ExtractResult(
        line_items=[],
        payment_terms="Net 30",
        validity_days=30,
        grand_total=0.0,
        injection_suspected=False,
    )


def _quote_mail(*, attachment_ids: list[str] | None = None) -> InboxEntry:
    return InboxEntry(
        id="in-p01",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Quote for RFQ-001",
        sim_time_hours=2.0,
        attachment_ids=attachment_ids or [],
    )


@pytest.mark.integration
def test_run_pass_downloads_attachments_before_extract(tmp_path: Path) -> None:
    store = RoundStore(tmp_path / "round")
    log = OperationalLog(tmp_path / "ops.jsonl")
    attachment = Attachment(
        id="att_02_0001",
        filename="Terms_addendum_1.pdf",
        mime_type="application/pdf",
        content=b"%PDF-1.4 terms",
    )
    simulator = _simulator(attachments={"att_02_0001": attachment})
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)
    simulator.push_inbox(_quote_mail(attachment_ids=["att_02_0001"]), body="see attached quote")
    extractor = FixtureExtractor({"in-p01": _quoted()})

    run_pass(simulator, store, extractor, log)

    assert extractor.requests[0].attachments[0].filename == "Terms_addendum_1.pdf"
    assert extractor.requests[0].attachments[0].content == b"%PDF-1.4 terms"


@pytest.mark.integration
def test_run_pass_retries_extract_when_quote_has_no_lines(tmp_path: Path) -> None:
    store = RoundStore(tmp_path / "round")
    log = OperationalLog(tmp_path / "ops.jsonl")
    simulator = _simulator()
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)
    simulator.push_inbox(
        _quote_mail(),
        body="qty 100 Steel I-Beam 200mm 40.00 USD\nqty 1 extra 0.00 USD",
    )
    run_pass(simulator, store, FixtureExtractor({"in-p01": _empty()}), log)
    first = store.load()
    assert first.suppliers["p01"].quote is not None
    assert first.suppliers["p01"].quote.as_sent.line_items == []
    assert first.suppliers["p01"].escalation_classes == []

    extractor = FixtureExtractor({"in-p01": _quoted()})
    run_pass(simulator, store, extractor, log)

    saved = store.load()
    assert saved.suppliers["p01"].quote is not None
    assert saved.suppliers["p01"].quote.as_sent.line_items[0].unit_price == 40.0
    assert extractor.requests


@pytest.mark.integration
def test_run_pass_does_not_retry_empty_quote_when_already_tried(tmp_path: Path) -> None:
    store = RoundStore(tmp_path / "round")
    log = OperationalLog(tmp_path / "ops.jsonl")
    simulator = _simulator()
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)
    simulator.push_inbox(
        _quote_mail(),
        body="qty 100 Steel I-Beam 200mm 40.00 USD\nqty 1 extra 0.00 USD",
    )
    retries: set[str] = set()
    run_pass(
        simulator,
        store,
        FixtureExtractor({"in-p01": _empty()}),
        log,
        empty_quote_retries=retries,
    )
    extractor = FixtureExtractor({"in-p01": _quoted()})
    run_pass(
        simulator,
        store,
        extractor,
        log,
        empty_quote_retries=retries,
    )

    assert extractor.requests == []
    saved = store.load()
    assert saved.suppliers["p01"].quote is not None
    assert saved.suppliers["p01"].quote.as_sent.line_items == []
