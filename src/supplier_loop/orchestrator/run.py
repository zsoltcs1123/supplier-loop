import time
from collections.abc import Callable
from typing import TextIO

from supplier_loop.extract.port import Extractor
from supplier_loop.extract.schema import ExtractAttachment
from supplier_loop.machine.advance import advance_suppliers, mark_quote_received
from supplier_loop.machine.answer import answer_question
from supplier_loop.machine.due import due_alarms
from supplier_loop.machine.happy import send_pending_rfqs
from supplier_loop.machine.negotiate import record_negotiation_reply
from supplier_loop.machine.remind import send_due_reminders
from supplier_loop.machine.ruling import handle_approver_ruling
from supplier_loop.mail_kind.classify import classify_mail
from supplier_loop.operational_log.log import OperationalLog
from supplier_loop.orchestrator.trigger import should_run_pass
from supplier_loop.progress import emit_progress
from supplier_loop.quote_pipeline.pipeline import process_inbound_mail
from supplier_loop.relevance import supplier_for_address
from supplier_loop.round_state.empty_quote import awaiting_empty_quote_retry
from supplier_loop.round_state.fingerprint import quote_fingerprint
from supplier_loop.round_state.models import RoundState
from supplier_loop.round_state.store import RoundStore
from supplier_loop.simulator.port import EmailMessage, InboxEntry, Simulator, SubmitEntry
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
    new_ids = [entry.id for entry in state.inbox if entry.id not in state.dedup.email_ids]
    sim_time = state.rfq.clock.sim_time_seconds
    if progress is not None:
        emit_progress(
            progress,
            sim_time_seconds=sim_time,
            kind="poll",
            subject=f"inbox={len(state.inbox)} new={len(new_ids)}",
        )
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
        echo = simulator.submit_results(payload)
        submitted = True
        sim_time = state.rfq.clock.sim_time_seconds
        log.record(
            round_id=state.rfq.clock.round_id,
            sim_time_seconds=sim_time,
            kind="submit",
            detail={"suppliers": sorted(payload), "warnings": list(echo.warnings)},
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
    pause_seconds: float = 0.0,
    sleeper: Callable[[float], None] | None = None,
) -> dict[str, SubmitEntry]:
    pause = sleeper or time.sleep
    for _ in range(max_passes):
        if run_pass(simulator, store, extractor, log, progress=progress):
            return build_submit_payload(store.load(), simulator)
        if pause_seconds > 0:
            pause(pause_seconds)
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
        retry = _needs_quote_retry(state, entry)
        if entry.id in state.dedup.email_ids and not retry:
            continue
        _ingest_entry(
            state,
            simulator,
            extractor,
            log,
            entry_id=entry.id,
            retry=retry,
            progress=progress,
        )


def _ingest_entry(
    state: RoundState,
    simulator: Simulator,
    extractor: Extractor,
    log: OperationalLog,
    *,
    entry_id: str,
    retry: bool,
    progress: TextIO | None,
) -> None:
    message = simulator.read_email(entry_id)
    if retry:
        state.dedup.quote_fingerprints.discard(quote_fingerprint(message))
    kind = _route_inbound(state, simulator, extractor, message)
    state.dedup.email_ids.add(entry_id)
    sim_time = state.rfq.clock.sim_time_seconds
    log.record(
        round_id=state.rfq.clock.round_id,
        sim_time_seconds=sim_time,
        kind="ingest",
        detail={"email_id": entry_id, "mail_kind": kind},
    )
    if progress is not None:
        emit_progress(
            progress,
            sim_time_seconds=sim_time,
            kind="ingest",
            subject=f"{entry_id} {kind} {message.from_address} {message.subject}",
        )


def _route_inbound(
    state: RoundState,
    simulator: Simulator,
    extractor: Extractor,
    message: EmailMessage,
) -> str:
    directory_entry = supplier_for_address(state, message.from_address)
    if directory_entry is not None:
        supplier = state.suppliers[directory_entry.supplier_id]
        kind = process_inbound_mail(
            message,
            supplier=supplier,
            rfq=state.rfq,
            dedup=state.dedup,
            extractor=extractor,
            attachments=_extract_attachments(simulator, message),
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
        return kind
    if message.from_address.casefold() == state.rfq.assignment.approver_email.casefold():
        handle_approver_ruling(message, state, simulator)
        return classify_mail(message, seen_fingerprints=state.dedup.quote_fingerprints)
    return "unknown"


def _needs_quote_retry(state: RoundState, entry: InboxEntry) -> bool:
    directory_entry = supplier_for_address(state, entry.from_address)
    if directory_entry is None:
        return False
    return awaiting_empty_quote_retry(state.suppliers[directory_entry.supplier_id])


def _extract_attachments(simulator: Simulator, message: EmailMessage) -> list[ExtractAttachment]:
    attachments: list[ExtractAttachment] = []
    for attachment_id in message.attachment_ids:
        downloaded = simulator.download_attachment(attachment_id)
        attachments.append(
            ExtractAttachment(
                filename=downloaded.filename,
                mime_type=downloaded.mime_type,
                content=downloaded.content,
            )
        )
    return attachments
