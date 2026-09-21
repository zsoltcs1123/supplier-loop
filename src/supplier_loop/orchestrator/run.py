from datetime import UTC, datetime
from typing import TextIO

from supplier_loop.extract.port import Extractor
from supplier_loop.machine.advance import advance_suppliers, mark_quote_received
from supplier_loop.machine.answer import answer_question
from supplier_loop.machine.due import due_alarms
from supplier_loop.machine.happy import send_pending_rfqs
from supplier_loop.machine.negotiate import record_negotiation_reply
from supplier_loop.machine.remind import send_due_reminders
from supplier_loop.machine.ruling import handle_approver_ruling
from supplier_loop.mail_kind.classify import classify_mail
from supplier_loop.operational_log.log import LogEvent, OperationalLog
from supplier_loop.orchestrator.trigger import should_run_pass
from supplier_loop.progress import emit_progress
from supplier_loop.quote_pipeline.pipeline import process_inbound_mail
from supplier_loop.relevance import supplier_for_address
from supplier_loop.round_state.models import RoundState
from supplier_loop.round_state.store import RoundStore
from supplier_loop.simulator.port import Simulator, SubmitEntry
from supplier_loop.submitter.submit import build_submit_payload, round_ready_to_submit


def run_pass(
    simulator: Simulator,
    store: RoundStore,
    extractor: Extractor,
    log: OperationalLog,
    *,
    progress: TextIO | None = None,
) -> bool:
    state = store.load()
    state.inbox = simulator.list_inbox()
    state.rfq.clock = simulator.get_sim_clock()
    if not should_run_pass(state):
        return False
    _ingest_inbox(state, simulator, extractor, log, progress=progress)
    send_pending_rfqs(state, simulator, log, progress=progress)
    if "reminder_due" in due_alarms(state):
        send_due_reminders(state, simulator, log, progress=progress)
    advance_suppliers(state, simulator)

    submitted = False
    if round_ready_to_submit(state):
        payload = build_submit_payload(state, simulator)
        simulator.submit_results(payload)
        submitted = True
        sim_time = state.rfq.clock.sim_time_seconds
        log.append(
            LogEvent(
                wall_time=datetime.now(UTC),
                sim_time_seconds=sim_time,
                kind="submit",
                detail={"suppliers": sorted(payload)},
            )
        )
        if progress is not None:
            emit_progress(
                progress,
                sim_time_seconds=sim_time,
                kind="submit",
                subject=f"{len(payload)} suppliers",
            )

    store.save(state)
    return submitted


def run_until_submit(
    simulator: Simulator,
    store: RoundStore,
    extractor: Extractor,
    log: OperationalLog,
    *,
    progress: TextIO | None = None,
    max_passes: int = 20,
) -> dict[str, SubmitEntry]:
    for _ in range(max_passes):
        if run_pass(simulator, store, extractor, log, progress=progress):
            return build_submit_payload(store.load(), simulator)
    raise RuntimeError("submit_results was not reached")


def _ingest_inbox(
    state: RoundState,
    simulator: Simulator,
    extractor: Extractor,
    log: OperationalLog,
    *,
    progress: TextIO | None = None,
) -> None:
    for entry in state.inbox:
        if entry.id in state.dedup.email_ids:
            continue
        message = simulator.read_email(entry.id)
        directory_entry = supplier_for_address(state, message.from_address)
        kind = "unknown"
        if directory_entry is not None:
            supplier = state.suppliers[directory_entry.supplier_id]
            kind = process_inbound_mail(
                message,
                supplier=supplier,
                rfq=state.rfq,
                dedup=state.dedup,
                extractor=extractor,
            )
            if kind == "quote" and supplier.quote is not None:
                mark_quote_received(
                    supplier,
                    sim_time_days=state.rfq.clock.sim_time_days,
                )
            elif kind == "question":
                answer_question(supplier, state, simulator, message)
            elif kind == "negotiation_reply":
                record_negotiation_reply(supplier, message)
            elif kind == "duplicate":
                pass
        elif message.from_address.casefold() == state.rfq.assignment.approver_email.casefold():
            kind = classify_mail(message, seen_fingerprints=state.dedup.quote_fingerprints)
            handle_approver_ruling(message, state, simulator)
        state.dedup.email_ids.add(entry.id)
        sim_time = state.rfq.clock.sim_time_seconds
        log.append(
            LogEvent(
                wall_time=datetime.now(UTC),
                sim_time_seconds=sim_time,
                kind="ingest",
                detail={"email_id": entry.id, "mail_kind": kind},
            )
        )
        if progress is not None:
            emit_progress(
                progress,
                sim_time_seconds=sim_time,
                kind="ingest",
                subject=f"{entry.id} {kind}",
            )
