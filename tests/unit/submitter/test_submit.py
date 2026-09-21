import pytest

from supplier_loop.round_state.models import (
    AsSentQuote,
    QuoteLine,
    QuoteRecord,
    SupplierFacts,
)
from supplier_loop.simulator.port import SentEmailRecord
from supplier_loop.submitter.submit import (
    build_submit_entry,
    derive_action_taken,
    derive_auto_approved,
)


def _supplier(*, escalation_classes: list[int] | None = None) -> SupplierFacts:
    escalation_classes = escalation_classes or []
    return SupplierFacts(
        supplier_id="p01",
        email="p01@sim.local",
        phase="done",
        escalation_classes=escalation_classes,
        quote=QuoteRecord(
            as_sent=AsSentQuote(
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
            ),
            recomputed_total=4000.0,
            recomputed_grand_total=4000.0,
        ),
    )


@pytest.mark.unit
def test_submitter_derives_extract_when_no_stronger_action() -> None:
    assert derive_action_taken(_supplier(), [], "approver@sim.local") == "extract"


@pytest.mark.unit
def test_submitter_derives_answered_question_when_question_was_answered() -> None:
    supplier = _supplier()
    supplier.question_answered = True

    assert derive_action_taken(supplier, [], "approver@sim.local") == "answered_question"


@pytest.mark.unit
def test_submitter_derives_reminded_when_reminder_was_sent() -> None:
    supplier = _supplier()
    supplier.reminder_sim_time = 90_000.0

    assert derive_action_taken(supplier, [], "approver@sim.local") == "reminded"


@pytest.mark.unit
def test_submitter_derives_escalated_when_ref_mail_sent() -> None:
    sent = [
        SentEmailRecord(
            id="sent-1",
            to="approver@sim.local",
            subject="Issue [REF:p01]",
            body="price high",
        )
    ]

    assert derive_action_taken(_supplier(), sent, "approver@sim.local") == "escalated"


@pytest.mark.unit
def test_submitter_auto_approved_true_when_clean_evidence() -> None:
    assert derive_auto_approved(_supplier(), [], "approver@sim.local") is True


@pytest.mark.unit
def test_submitter_auto_approved_false_when_escalation_classes_present() -> None:
    assert (
        derive_auto_approved(_supplier(escalation_classes=[5]), [], "approver@sim.local") is False
    )


@pytest.mark.unit
def test_submitter_auto_approved_false_when_escalation_mail_without_approval() -> None:
    sent = [
        SentEmailRecord(
            id="sent-1",
            to="approver@sim.local",
            subject="[REF:p01] class 1",
            body="Class 1: missing BOM line(s): STL-BEAM-200.",
        )
    ]
    supplier = _supplier(escalation_classes=[1])

    assert derive_auto_approved(supplier, sent, "approver@sim.local") is False


@pytest.mark.unit
def test_submitter_auto_approved_true_when_approver_approved_after_escalation() -> None:
    sent = [
        SentEmailRecord(
            id="sent-1",
            to="approver@sim.local",
            subject="[REF:p01] class 1",
            body="Class 1: missing BOM line(s): STL-BEAM-200.",
        )
    ]
    supplier = _supplier(escalation_classes=[1])
    supplier.approver_rulings = ["Approved. Class 1 looks fine now."]

    assert derive_auto_approved(supplier, sent, "approver@sim.local") is True


@pytest.mark.unit
def test_submitter_auto_approved_false_when_approver_asks_for_specifics() -> None:
    sent = [
        SentEmailRecord(
            id="sent-1",
            to="approver@sim.local",
            subject="[REF:p01] class 1",
            body="Class 1: missing BOM line(s): STL-BEAM-200.",
        )
    ]
    supplier = _supplier(escalation_classes=[1])
    supplier.approver_rulings = [
        "I need specifics before I can rule on this — tell me exactly what looks wrong."
    ]

    assert derive_auto_approved(supplier, sent, "approver@sim.local") is False


@pytest.mark.unit
def test_submitter_builds_entry_with_recomputed_totals() -> None:
    entry = build_submit_entry(_supplier(), [], "approver@sim.local")

    assert entry.action_taken == "extract"
    assert entry.auto_approved is True
    assert entry.line_items[0].total == 4000.0
    assert entry.grand_total == 4000.0
    assert entry.payment_terms == "Net 30"
    assert entry.validity_days == 14


@pytest.mark.unit
def test_submitter_uses_revised_as_sent_when_present() -> None:
    supplier = _supplier()
    assert supplier.quote is not None
    supplier.quote.revised_as_sent = AsSentQuote(
        line_items=[
            QuoteLine(
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                quantity=100.0,
                unit_price=42.0,
                total=4200.0,
            )
        ],
        payment_terms="Net 30",
        validity_days=21,
        grand_total=4200.0,
    )
    supplier.quote.recomputed_total = 4200.0
    supplier.quote.recomputed_grand_total = 4200.0

    entry = build_submit_entry(supplier, [], "approver@sim.local")

    assert entry.line_items[0].unit_price == 42.0
    assert entry.validity_days == 21
    assert entry.grand_total == 4200.0
