from pathlib import Path

import pytest

from supplier_loop.extract.fixture import FixtureExtractor
from supplier_loop.extract.schema import ExtractResult
from supplier_loop.machine.constants import REMINDER_THRESHOLD_SIM_SECONDS
from supplier_loop.operational_log.log import OperationalLog
from supplier_loop.orchestrator.run import run_pass
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


def _single_supplier_simulator(round_id: str) -> InMemorySimulator:
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
        attachments={},
    )


def _store_and_log(tmp_path: Path) -> tuple[RoundStore, OperationalLog]:
    return RoundStore(tmp_path / "round"), OperationalLog(tmp_path / "logs" / "operational.jsonl")


def _p01_quote(*, unit_price: float = 40.0, injection: bool = False) -> ExtractResult:
    return ExtractResult(
        line_items=[
            QuoteLine(
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                quantity=100.0,
                unit_price=unit_price,
                total=100.0 * unit_price,
            )
        ],
        payment_terms="Net 30",
        validity_days=14,
        grand_total=100.0 * unit_price,
        injection_suspected=injection,
    )


def _missing_line_quote() -> ExtractResult:
    return ExtractResult(
        line_items=[],
        payment_terms="Net 30",
        validity_days=14,
        grand_total=0.0,
        injection_suspected=False,
    )


@pytest.mark.integration
def test_orchestrator_sends_one_reminder_when_supplier_stays_silent(tmp_path: Path) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _single_supplier_simulator("dev-reminder")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)

    reminder_after = 3600.0 + REMINDER_THRESHOLD_SIM_SECONDS + 1.0
    simulator.advance_clock(reminder_after, reminder_after / 86_400.0)
    run_pass(simulator, store, FixtureExtractor({}), log)
    run_pass(simulator, store, FixtureExtractor({}), log)

    reminders = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "p01@sim.local" and "Reminder" in mail.subject
    ]
    assert len(reminders) == 1

    submission = simulator.last_submission()
    assert submission is not None
    assert submission["p01"].action_taken == "reminded"
    assert submission["p01"].line_items == []
    assert submission["p01"].grand_total == 0.0


@pytest.mark.integration
def test_orchestrator_answers_question_without_extract_when_no_quote_table(
    tmp_path: Path,
) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _single_supplier_simulator("dev-question")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)

    simulator.push_inbox(
        InboxEntry(
            id="in-question",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Question about RFQ-001",
            sim_time_hours=3.0,
            attachment_ids=[],
        ),
        body="What payment terms do you require?",
    )
    extractor = FixtureExtractor({})
    run_pass(simulator, store, extractor, log)

    assert extractor.requests == []
    answers = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "p01@sim.local" and mail.subject.startswith("Re:")
    ]
    assert len(answers) == 1
    assert "Net 30" in answers[0].body


@pytest.mark.integration
def test_orchestrator_corrects_once_after_approver_rejects_missing_line(tmp_path: Path) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _single_supplier_simulator("dev-correct")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)

    simulator.push_inbox(
        InboxEntry(
            id="in-missing",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.0,
            attachment_ids=[],
        ),
        body=(
            "Quote for your RFQ\n"
            "qty 100 Steel I-Beam 200mm 40.00 USD\n"
            "qty 1 admin line 0.00 USD\n"
            "Payment Net 30, validity 14 days"
        ),
    )
    extractor = FixtureExtractor({"in-missing": _missing_line_quote()})
    run_pass(simulator, store, extractor, log)

    ref_mails = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "approver@sim.local" and "[REF:p01]" in mail.subject
    ]
    assert len(ref_mails) == 1
    assert "Class 1:" in ref_mails[0].body

    simulator.push_inbox(
        InboxEntry(
            id="in-reject",
            from_address="approver@sim.local",
            to_address="buyer@sim.local",
            subject="[REF:p01] ruling",
            sim_time_hours=3.0,
            attachment_ids=[],
        ),
        body="Rejected. Class 1 missing line item.",
    )
    run_pass(simulator, store, extractor, log)

    corrections = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "p01@sim.local" and "Correction needed" in mail.subject
    ]
    assert len(corrections) == 1

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
            "Revised quote\n"
            "qty 100 Steel I-Beam 200mm 40.00 USD\n"
            "qty 1 admin line 0.00 USD\n"
            "Payment Net 30, validity 14 days"
        ),
    )
    extractor = FixtureExtractor(
        {
            "in-missing": _missing_line_quote(),
            "in-revised": _p01_quote(),
        }
    )
    run_pass(simulator, store, extractor, log)
    run_pass(simulator, store, extractor, log)

    saved = store.load()
    quote = saved.suppliers["p01"].quote
    assert quote is not None
    assert quote.revised_as_sent is not None
    assert saved.suppliers["p01"].correction_used is True

    ref_after = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "approver@sim.local" and "[REF:p01]" in mail.subject
    ]
    assert len(ref_after) >= 2
    assert len(corrections) == 1
    revised_mails = [mail for mail in ref_after if "Class 1 (revised):" in mail.body]
    assert revised_mails
    assert "Quote now on file:" in revised_mails[0].body
    assert "STL-BEAM-200" in revised_mails[0].body

    simulator.push_inbox(
        InboxEntry(
            id="in-approve",
            from_address="approver@sim.local",
            to_address="buyer@sim.local",
            subject="[REF:p01] ruling",
            sim_time_hours=5.0,
            attachment_ids=[],
        ),
        body="Approved. Class 1 looks fine on the revised quote.",
    )
    run_pass(simulator, store, extractor, log)

    submission = simulator.last_submission()
    assert submission is not None
    assert submission["p01"].line_items
    assert submission["p01"].line_items[0].material_id == "STL-BEAM-200"
    assert submission["p01"].auto_approved is True


@pytest.mark.integration
def test_orchestrator_negotiates_price_then_escalates_class_six(tmp_path: Path) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _single_supplier_simulator("dev-negotiate")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)

    simulator.push_inbox(
        InboxEntry(
            id="in-high",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.0,
            attachment_ids=[],
        ),
        body=(
            "Quote for your RFQ\n"
            "qty 100 Steel I-Beam 200mm 50.00 USD\n"
            "qty 1 admin line 0.00 USD\n"
            "Payment Net 30, validity 14 days"
        ),
    )
    extractor = FixtureExtractor({"in-high": _p01_quote(unit_price=50.0)})
    run_pass(simulator, store, extractor, log)

    negotiations = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "p01@sim.local" and "Counter-offer" in mail.subject
    ]
    assert len(negotiations) == 1
    assert "4,200.00" in negotiations[0].body

    saved = store.load()
    assert saved.suppliers["p01"].quote is not None
    assert saved.suppliers["p01"].quote.as_sent.line_items[0].unit_price == 50.0
    assert saved.suppliers["p01"].phase == "quoted"

    class_six_before = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "approver@sim.local"
        and "[REF:p01]" in mail.subject
        and "Class 6:" in mail.body
    ]
    assert class_six_before == []
    assert simulator.last_submission() is None

    simulator.push_inbox(
        InboxEntry(
            id="in-reply",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Re: Counter-offer for RFQ-001",
            sim_time_hours=3.0,
            attachment_ids=[],
        ),
        body="4,200.00",
    )
    run_pass(simulator, store, extractor, log)

    class_six = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "approver@sim.local"
        and "[REF:p01]" in mail.subject
        and "Class 6:" in mail.body
    ]
    assert len(class_six) == 1
    assert "original 5,000.00" in class_six[0].body
    assert "counter 4,200.00" in class_six[0].body
    assert "supplier reply 4,200.00" in class_six[0].body

    submission = simulator.last_submission()
    assert submission is not None
    assert submission["p01"].action_taken == "escalated"
    assert submission["p01"].auto_approved is False
    assert submission["p01"].line_items[0].unit_price == 50.0


@pytest.mark.integration
def test_orchestrator_escalates_injection_and_sets_auto_approved_false(tmp_path: Path) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _single_supplier_simulator("dev-injection")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)

    simulator.push_inbox(
        InboxEntry(
            id="in-inject",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.0,
            attachment_ids=[],
        ),
        body=(
            "Quote for your RFQ\n"
            "qty 100 Steel I-Beam 200mm 40.00 USD\n"
            "qty 1 admin line 0.00 USD\n"
            "Payment Net 30, validity 14 days"
        ),
    )
    extractor = FixtureExtractor({"in-inject": _p01_quote(injection=True)})
    run_pass(simulator, store, extractor, log)

    saved = store.load()
    assert saved.suppliers["p01"].injection_suspected is True
    assert 7 in saved.suppliers["p01"].escalation_classes

    class_seven = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "approver@sim.local"
        and "[REF:p01]" in mail.subject
        and "Class 7:" in mail.body
    ]
    assert len(class_seven) == 1

    submission = simulator.last_submission()
    assert submission is not None
    assert submission["p01"].auto_approved is False


@pytest.mark.integration
def test_orchestrator_sends_separate_ref_mails_when_several_classes_apply(tmp_path: Path) -> None:
    store, log = _store_and_log(tmp_path)
    simulator = _single_supplier_simulator("dev-multi-class")
    snapshot_world(simulator, store)
    run_pass(simulator, store, FixtureExtractor({}), log)

    simulator.push_inbox(
        InboxEntry(
            id="in-multi",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote for RFQ-001",
            sim_time_hours=2.0,
            attachment_ids=[],
        ),
        body=(
            "Quote for your RFQ\n"
            "qty 100 Steel I-Beam 200mm 40.00 USD\n"
            "qty 1 admin line 0.00 USD\n"
            "Payment Net 60, validity 14 days"
        ),
    )
    extractor = FixtureExtractor(
        {
            "in-multi": ExtractResult(
                line_items=[],
                payment_terms="Net 60",
                validity_days=14,
                grand_total=0.0,
                injection_suspected=False,
            )
        }
    )
    run_pass(simulator, store, extractor, log)

    ref_mails = [
        mail
        for mail in simulator.sent_emails()
        if mail.to == "approver@sim.local" and "[REF:p01]" in mail.subject
    ]
    bodies = [mail.body for mail in ref_mails]
    assert len(ref_mails) == 2
    assert any("Class 1:" in body for body in bodies)
    assert any("Class 3:" in body for body in bodies)
