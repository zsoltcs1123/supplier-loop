from typing import cast

import pytest

from supplier_loop.machine.constants import (
    PDF_PHOTO_QUIET_MARGIN_SIM_SECONDS,
    PDF_PHOTO_REMINDER_THRESHOLD_SIM_SECONDS,
    QUIET_MARGIN_SIM_SECONDS,
    REMINDER_THRESHOLD_SIM_SECONDS,
    VALIDITY_ALARM_MARGIN_DAYS,
)
from supplier_loop.machine.correct import correct_once
from supplier_loop.machine.due import due_alarms
from supplier_loop.machine.remind import send_due_reminders
from supplier_loop.operational_log.log import OperationalLog
from supplier_loop.round_state.models import (
    AsSentQuote,
    DedupRegistry,
    QuoteLine,
    QuoteRecord,
    RfqContext,
    RoundState,
    SupplierFacts,
    SupplierPhase,
)
from supplier_loop.simulator.port import (
    Assignment,
    BomLine,
    SimClock,
    Simulator,
    SupplierEntry,
)


def _round_state(
    *,
    phase: SupplierPhase = "awaiting_quote",
    sim_seconds: float = 100_000.0,
) -> RoundState:
    supplier = SupplierFacts(
        supplier_id="p01",
        email="p01@sim.local",
        phase=phase,
        awaiting_since_sim_time=3600.0,
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
            price_history=[],
            clock=SimClock(
                sim_time_seconds=sim_seconds,
                sim_time_days=sim_seconds / 86_400.0,
                round_id="dev-1",
                mode="development",
                clock_factor=60.0,
            ),
        ),
        suppliers={"p01": supplier},
        inbox=[],
        dedup=DedupRegistry(),
    )


@pytest.mark.unit
def test_due_alarms_returns_reminder_due_when_threshold_passed() -> None:
    state = _round_state(sim_seconds=3600.0 + REMINDER_THRESHOLD_SIM_SECONDS)

    assert "reminder_due" in due_alarms(state)


def _as_pdf_supplier(state: RoundState) -> RoundState:
    state.rfq.directory[0] = SupplierEntry(
        supplier_id="p03",
        email="y.tanaka@tanakaprecision.example",
        material_ids=["STL-BEAM-200"],
    )
    supplier = state.suppliers.pop("p01")
    supplier.supplier_id = "p03"
    supplier.email = "y.tanaka@tanakaprecision.example"
    state.suppliers["p03"] = supplier
    return state


@pytest.mark.unit
def test_due_alarms_holds_pdf_supplier_past_text_reminder_threshold() -> None:
    state = _as_pdf_supplier(_round_state(sim_seconds=3600.0 + REMINDER_THRESHOLD_SIM_SECONDS))

    assert "reminder_due" not in due_alarms(state)

    state.rfq.clock.sim_time_seconds = 3600.0 + PDF_PHOTO_REMINDER_THRESHOLD_SIM_SECONDS
    assert "reminder_due" in due_alarms(state)


@pytest.mark.unit
def test_due_alarms_holds_pdf_supplier_past_one_quiet_day() -> None:
    reminder_at = 90_000.0
    state = _as_pdf_supplier(_round_state(sim_seconds=reminder_at + QUIET_MARGIN_SIM_SECONDS))
    state.suppliers["p03"].reminder_sim_time = reminder_at

    assert "round_done" not in due_alarms(state)

    state.rfq.clock.sim_time_seconds = reminder_at + PDF_PHOTO_QUIET_MARGIN_SIM_SECONDS
    assert "round_done" in due_alarms(state)


@pytest.mark.unit
def test_due_alarms_skips_second_reminder_when_already_sent() -> None:
    state = _round_state(sim_seconds=3600.0 + REMINDER_THRESHOLD_SIM_SECONDS + 100.0)
    state.suppliers["p01"].reminder_sim_time = 90_000.0

    assert "reminder_due" not in due_alarms(state)


@pytest.mark.unit
def test_due_alarms_skips_round_done_when_reminder_wait_is_open() -> None:
    state = _round_state(sim_seconds=90_001.0)
    state.suppliers["p01"].reminder_sim_time = 90_000.0

    assert "round_done" not in due_alarms(state)


@pytest.mark.unit
def test_due_alarms_returns_round_done_when_reminded_and_quiet_margin_elapsed() -> None:
    reminder_at = 90_000.0
    state = _round_state(sim_seconds=reminder_at + QUIET_MARGIN_SIM_SECONDS)
    state.suppliers["p01"].reminder_sim_time = reminder_at

    assert "round_done" in due_alarms(state)


@pytest.mark.unit
def test_due_alarms_returns_validity_alarm_when_quote_near_expiry() -> None:
    state = _round_state(phase="quoted", sim_seconds=10_000.0)
    supplier = state.suppliers["p01"]
    supplier.quote_received_sim_days = 0.0
    supplier.quote = QuoteRecord(
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
            validity_days=int(VALIDITY_ALARM_MARGIN_DAYS),
            grand_total=4000.0,
        ),
        recomputed_total=4000.0,
        recomputed_grand_total=4000.0,
    )
    state.rfq.clock.sim_time_days = VALIDITY_ALARM_MARGIN_DAYS

    assert "validity_alarm" in due_alarms(state)


@pytest.mark.unit
def test_correct_once_is_noop_when_correction_already_used() -> None:
    state = _round_state(phase="escalated")
    supplier = state.suppliers["p01"]
    supplier.correction_used = True
    supplier.quote = QuoteRecord(
        as_sent=AsSentQuote(
            line_items=[],
            payment_terms="Net 30",
            validity_days=14,
            grand_total=0.0,
        ),
        recomputed_total=0.0,
        recomputed_grand_total=0.0,
    )

    class _Sim:
        def send_email(self, to: str, subject: str, body: str) -> str:
            raise AssertionError("send_email should not run")

    assert correct_once(supplier, state, cast(Simulator, _Sim()), 1) is False


@pytest.mark.unit
def test_send_due_reminders_is_noop_when_reminder_already_sent() -> None:
    state = _round_state(sim_seconds=3600.0 + REMINDER_THRESHOLD_SIM_SECONDS + 100.0)
    state.suppliers["p01"].reminder_sim_time = 90_000.0

    class _Sim:
        def send_email(self, to: str, subject: str, body: str) -> str:
            raise AssertionError("send_email should not run")

    class _Log:
        def append(self, event: object) -> None:
            raise AssertionError("log append should not run")

    send_due_reminders(state, cast(Simulator, _Sim()), cast(OperationalLog, _Log()))
