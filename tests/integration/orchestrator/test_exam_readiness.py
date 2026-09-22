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
from tests.unit.sample_traffic import load_sample_email


def _simulator(
    round_id: str, *, attachments: dict[str, Attachment] | None = None
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
        ],
        history=[
            PriceHistoryRow(
                supplier_id="p01",
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=40.0,
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
        attachments=attachments or {},
    )


def _store_and_log(tmp_path: Path) -> tuple[RoundStore, OperationalLog]:
    return RoundStore(tmp_path / "round"), OperationalLog(tmp_path / "logs" / "operational.jsonl")


def _clean_quote() -> ExtractResult:
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


def _empty_quote() -> ExtractResult:
    return ExtractResult(
        line_items=[],
        payment_terms="",
        validity_days=0,
        grand_total=0.0,
        injection_suspected=False,
    )


def _terms_quote() -> ExtractResult:
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
        payment_terms="Net 60",
        validity_days=14,
        grand_total=4000.0,
        injection_suspected=False,
    )


def _approver_mails(simulator: InMemorySimulator) -> list[str]:
    return [
        mail.body
        for mail in simulator.sent_emails()
        if mail.to == "approver@sim.local" and "[REF:p01]" in mail.subject
    ]


@pytest.mark.integration
def test_orchestrator_escalates_class_7_from_body_when_extract_flag_is_false(
    tmp_path: Path,
) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _simulator(
        "dev-scan",
        attachments={
            "att-014": Attachment(
                id="att-014",
                filename="quote.pdf",
                mime_type="application/pdf",
                content=b"%PDF",
            )
        },
    )
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)
    trap = load_sample_email("sample-014")
    simulator.push_inbox(
        InboxEntry(
            id="in-inject",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.0,
            attachment_ids=["att-014"],
        ),
        body=trap.body,
    )
    run_pass(simulator, store, FixtureExtractor({"in-inject": _clean_quote()}), log)

    saved = store.load()
    assert saved.suppliers["p01"].injection_suspected is True
    assert saved.suppliers["p01"].injection_phrase is not None
    bodies = _approver_mails(simulator)
    assert len(bodies) == 1
    assert "Class 7:" in bodies[0]
    assert "exempt from the approval" in bodies[0].casefold()
    assert simulator.last_submission() is None

    simulator.push_inbox(
        InboxEntry(
            id="in-class7-ruling",
            from_address="approver@sim.local",
            to_address="buyer@sim.local",
            subject="[REF:p01] ruling",
            sim_time_hours=3.0,
            attachment_ids=[],
        ),
        body="Rejected. Class 7. Do not follow the embedded instruction.",
    )
    run_pass(simulator, store, FixtureExtractor({"in-inject": _clean_quote()}), log)
    submission = simulator.last_submission()
    assert submission is not None
    assert submission["p01"].action_taken == "escalated"
    assert submission["p01"].auto_approved is False


@pytest.mark.integration
def test_orchestrator_does_not_escalate_terms_when_first_extract_has_no_lines(
    tmp_path: Path,
) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _simulator("dev-empty")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)
    simulator.push_inbox(
        InboxEntry(
            id="in-p01",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.0,
            attachment_ids=[],
        ),
        body=("see attached quote\nqty 100 Steel I-Beam 200mm 40.00 USD\nqty 1 extra 0.00 USD"),
    )
    run_pass(simulator, store, FixtureExtractor({"in-p01": _empty_quote()}), log)

    first = store.load()
    assert first.suppliers["p01"].quote is not None
    assert first.suppliers["p01"].quote.as_sent.line_items == []
    assert first.suppliers["p01"].escalation_classes == []
    assert simulator.last_submission() is None
    assert _approver_mails(simulator) == []

    run_pass(simulator, store, FixtureExtractor({"in-p01": _clean_quote()}), log)
    saved = store.load()
    assert saved.suppliers["p01"].quote is not None
    assert saved.suppliers["p01"].quote.as_sent.line_items[0].unit_price == 40.0
    assert _approver_mails(simulator) == []


@pytest.mark.integration
def test_orchestrator_re_escalation_after_correction_does_not_claim_matched_terms(
    tmp_path: Path,
) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _simulator("dev-revised-terms")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)
    simulator.push_inbox(
        InboxEntry(
            id="in-terms",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.0,
            attachment_ids=[],
        ),
        body=(
            "qty 100 Steel I-Beam 200mm 40.00 USD\n"
            "qty 1 extra 0.00 USD\n"
            "Payment Net 60, validity 14 days"
        ),
    )
    run_pass(simulator, store, FixtureExtractor({"in-terms": _terms_quote()}), log)
    assert any("Class 3:" in body for body in _approver_mails(simulator))

    simulator.push_inbox(
        InboxEntry(
            id="in-reject",
            from_address="approver@sim.local",
            to_address="buyer@sim.local",
            subject="[REF:p01] ruling",
            sim_time_hours=3.0,
            attachment_ids=[],
        ),
        body="Rejected. Class 3. Ask for Net 30.",
    )
    run_pass(simulator, store, FixtureExtractor({"in-terms": _terms_quote()}), log)

    simulator.push_inbox(
        InboxEntry(
            id="in-revised",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Re: Correction needed for RFQ-001",
            sim_time_hours=4.0,
            attachment_ids=[],
        ),
        body=(
            "qty 100 Steel I-Beam 200mm 40.00 USD\n"
            "qty 1 extra 0.00 USD\n"
            "Payment Net 30, validity 14 days"
        ),
    )
    extractor = FixtureExtractor({"in-terms": _terms_quote(), "in-revised": _clean_quote()})
    run_pass(simulator, store, extractor, log)
    run_pass(simulator, store, extractor, log)

    revised = [body for body in _approver_mails(simulator) if "Class 3 (revised):" in body]
    assert revised
    assert "Quote now on file:" in revised[0]
    assert "differs" not in revised[0]


@pytest.mark.integration
def test_orchestrator_sends_no_approver_mail_before_a_quote_is_stored(tmp_path: Path) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _simulator("dev-premature")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)

    rfqs = [mail for mail in simulator.sent_emails() if mail.to == "p01@sim.local"]
    assert rfqs
    assert _approver_mails(simulator) == []

    simulator.advance_clock(10_000.0, 10_000.0 / 86_400.0)
    run_pass(simulator, store, FixtureExtractor({}), log)

    assert _approver_mails(simulator) == []
    assert store.load().suppliers["p01"].quote is None
    assert not any("[REF:" in mail.subject for mail in simulator.sent_emails())
