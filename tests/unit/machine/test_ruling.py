from typing import cast

import pytest

from supplier_loop.machine.ruling import (
    handle_approver_ruling,
    is_approval_ruling,
    is_rejection_ruling,
)
from supplier_loop.round_state.models import (
    AsSentQuote,
    DedupRegistry,
    QuoteLine,
    QuoteRecord,
    RfqContext,
    RoundState,
    SupplierFacts,
)
from supplier_loop.simulator.port import (
    Assignment,
    BomLine,
    EmailMessage,
    SentEmailRecord,
    SimClock,
    Simulator,
    SupplierEntry,
)

_NOT_APPROVING = (
    "Yes, the quantity is off versus what we requested. "
    "Not approving that — have them requote at the right quantity."
)


@pytest.mark.unit
def test_ruling_treats_not_approving_as_rejection() -> None:
    assert is_rejection_ruling(_NOT_APPROVING) is True
    assert is_approval_ruling(_NOT_APPROVING) is False


@pytest.mark.unit
def test_ruling_treats_approved_as_approval() -> None:
    body = "Approved. Class 1 looks fine now."

    assert is_rejection_ruling(body) is False
    assert is_approval_ruling(body) is True


@pytest.mark.unit
def test_ruling_sends_correction_when_approver_says_not_approving() -> None:
    state = _quoted_state()
    sent: list[tuple[str, str, str]] = []

    class _Sim:
        def send_email(self, to: str, subject: str, body: str) -> str:
            sent.append((to, subject, body))
            return "out-1"

    handle_approver_ruling(
        EmailMessage(
            id="in-ruling",
            from_address="approver@sim.local",
            to_address="buyer@sim.local",
            subject="[REF:p02] ruling",
            sim_time_hours=4.0,
            attachment_ids=[],
            body=_NOT_APPROVING,
        ),
        state,
        cast(Simulator, _Sim()),
    )

    assert state.suppliers["p02"].correction_used is True
    assert state.suppliers["p02"].phase == "escalated"
    assert len(sent) == 1
    assert sent[0][0] == "declan@emeraldfittings.example"
    assert "quantity" in sent[0][2].casefold()


_NEED_SPECIFICS = (
    "Hi, I need specifics before I can rule on this — "
    "tell me exactly what looks wrong with their quote and I'll confirm."
)


@pytest.mark.unit
def test_ruling_restates_class_six_claim_once_when_approver_asks_for_specifics() -> None:
    state = _quoted_state()
    supplier = state.suppliers["p02"]
    supplier.escalation_classes = [6]
    supplier.negotiation_target_total = 4116.0
    supplier.negotiation_reply_total = 4116.0
    supplier.escalation_wait_since_sim_seconds = 0.0
    assert supplier.quote is not None
    supplier.quote.recomputed_grand_total = 3951.60
    sent: list[tuple[str, str, str]] = []
    simulator = _recording_simulator(sent)
    ruling = _specifics_message()

    handle_approver_ruling(ruling, state, simulator)
    handle_approver_ruling(ruling, state, simulator)

    assert len(sent) == 1
    assert sent[0][0] == "approver@sim.local"
    assert sent[0][1] == "[REF:p02] class 6"
    assert sent[0][2].startswith("Specifics: ")
    assert "supplier reply 4,116.00" in sent[0][2]
    assert "differs from original 14,996.80" in sent[0][2]
    assert "counter 4,116.00" in sent[0][2]
    assert supplier.phase == "escalated"
    assert supplier.escalation_wait_since_sim_seconds == 10_000.0


@pytest.mark.unit
def test_ruling_stays_quiet_when_specifics_request_has_no_discrepancy() -> None:
    state = _quoted_state()
    state.suppliers["p02"].escalation_classes = [1]
    sent: list[tuple[str, str, str]] = []

    handle_approver_ruling(_specifics_message(), state, _recording_simulator(sent))

    assert sent == []
    assert state.suppliers["p02"].phase == "escalated"


def _specifics_message() -> EmailMessage:
    return EmailMessage(
        id="in-specifics",
        from_address="approver@sim.local",
        to_address="buyer@sim.local",
        subject="[REF:p02] ruling",
        sim_time_hours=4.0,
        attachment_ids=[],
        body=_NEED_SPECIFICS,
    )


def _recording_simulator(sent: list[tuple[str, str, str]]) -> Simulator:
    class _Sim:
        def send_email(self, to: str, subject: str, body: str) -> str:
            sent.append((to, subject, body))
            return f"out-{len(sent)}"

        def list_sent(self) -> list[SentEmailRecord]:
            return [
                SentEmailRecord(id=f"sent-{index}", to=to, subject=subject, body=body)
                for index, (to, subject, body) in enumerate(sent, start=1)
            ]

    return cast(Simulator, _Sim())


def _quoted_state() -> RoundState:
    quote = QuoteRecord(
        as_sent=AsSentQuote(
            line_items=[
                QuoteLine(
                    material_id="AL-SHEET-3",
                    description="Aluminum Sheet 3mm",
                    quantity=260.0,
                    unit_price=57.68,
                    total=14996.8,
                )
            ],
            payment_terms="Net 30",
            validity_days=14,
            grand_total=14996.8,
        ),
        recomputed_total=14996.8,
        recomputed_grand_total=14996.8,
    )
    return RoundState(
        rfq=RfqContext(
            assignment=Assignment(
                rfq_id="RFQ-001",
                required_payment_terms="Net 30",
                required_validity_days=14,
                target_price_ceiling_pct=5.0,
                line_items=[
                    BomLine(
                        material_id="AL-SHEET-3",
                        description="Aluminum Sheet 3mm",
                        unit="sheet",
                        quantity=200.0,
                    )
                ],
                goal_statement="Cover the BOM",
                approver_email="approver@sim.local",
                escalation_subject_protocol="[REF:<supplier_id>]",
            ),
            directory=[
                SupplierEntry(
                    supplier_id="p02",
                    email="declan@emeraldfittings.example",
                    material_ids=["AL-SHEET-3"],
                )
            ],
            price_history=[],
            clock=SimClock(
                sim_time_seconds=10_000.0,
                sim_time_days=0.1,
                round_id="dev-1",
                mode="development",
                clock_factor=60.0,
            ),
        ),
        suppliers={
            "p02": SupplierFacts(
                supplier_id="p02",
                email="declan@emeraldfittings.example",
                phase="escalated",
                escalation_classes=[2],
                quote=quote,
            )
        },
        inbox=[],
        dedup=DedupRegistry(),
    )
