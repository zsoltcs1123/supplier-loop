import json
from pathlib import Path
from typing import TextIO

from supplier_loop.extract.spend import SpendLedger, load_spend
from supplier_loop.machine.constants import (
    ESCALATION_SETTLE_SIM_SECONDS,
    NEGOTIATION_REPLY_SIM_DAYS,
    PDF_PHOTO_QUIET_MARGIN_SIM_SECONDS,
    PDF_PHOTO_REMINDER_THRESHOLD_SIM_SECONDS,
    QUIET_MARGIN_SIM_SECONDS,
    REMINDER_THRESHOLD_SIM_SECONDS,
)
from supplier_loop.operational_log.log import LogEvent, OperationalLog
from supplier_loop.round_state.models import RoundState
from supplier_loop.round_state.store import RoundStore

ALLOW_LIST = (
    "reminder",
    "quiet margin",
    "settle wait",
    "negotiation wait",
    "SOP wording",
    "Never list",
)
OUT_OF_SCOPE = ("escalation classes", "start_exam")

_SIM_DAY = 86_400.0


def write_pack(*, artifacts_root: Path, out: TextIO | None = None) -> Path:
    store = RoundStore(artifacts_root / "round")
    try:
        state = store.load()
    except FileNotFoundError as exc:
        raise SystemExit(f"No round state at {store.root / 'round.json'}") from exc
    round_id = state.rfq.clock.round_id
    events = OperationalLog(artifacts_root / "ops.jsonl").events_for_round(round_id)
    spend = load_spend(artifacts_root / "llm-spend.json")
    path = artifacts_root / "proposals" / round_id / "pack.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_pack(state, events, spend), encoding="utf-8")
    if out is not None:
        out.write(f"{path}\n")
    return path


def render_pack(state: RoundState, events: list[LogEvent], spend: SpendLedger) -> str:
    round_id = state.rfq.clock.round_id
    lines = [
        f"# Proposal pack {round_id}",
        "",
        f"round_id: {round_id}",
        f"mode: {state.rfq.clock.mode}",
        f"rfq_id: {state.rfq.assignment.rfq_id}",
        "",
        "## Allow-list",
        "",
    ]
    lines.extend(f"- {item}" for item in ALLOW_LIST)
    lines.extend(
        [
            "",
            "Out of scope: " + ", ".join(OUT_OF_SCOPE) + ".",
            "",
            "## Current clock",
            "",
            (
                f"- reminder: {_sim_days(REMINDER_THRESHOLD_SIM_SECONDS)} (p01, p02); "
                f"{_sim_days(PDF_PHOTO_REMINDER_THRESHOLD_SIM_SECONDS)} (p03, p04)"
            ),
            (
                f"- quiet margin: {_sim_days(QUIET_MARGIN_SIM_SECONDS)} (p01, p02); "
                f"{_sim_days(PDF_PHOTO_QUIET_MARGIN_SIM_SECONDS)} (p03, p04)"
            ),
            f"- settle wait: {_sim_days(ESCALATION_SETTLE_SIM_SECONDS)}",
            f"- negotiation wait: {_days(NEGOTIATION_REPLY_SIM_DAYS)}",
            "",
            "## Suppliers",
            "",
        ]
    )
    for supplier_id, facts in sorted(state.suppliers.items()):
        lines.append(f"- {supplier_id}: {facts.phase}")
    lines.extend(["", "## Submit warnings", ""])
    warnings = _submit_warnings(events)
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("(none)")
    lines.extend(
        [
            "",
            "## Extract spend",
            "",
            f"used={spend.used:.4f} cap={spend.cap:g} remaining={spend.remaining:.4f}",
            "",
            "## Operational log",
            "",
        ]
    )
    if events:
        lines.extend(_log_line(event) for event in events)
    else:
        lines.append("(none)")
    lines.append("")
    return "\n".join(lines)


def _submit_warnings(events: list[LogEvent]) -> list[str]:
    warnings: list[str] = []
    for event in events:
        if event.kind != "submit":
            continue
        raw = event.detail.get("warnings", [])
        if isinstance(raw, list):
            warnings.extend(str(item) for item in raw)
        elif raw:
            warnings.append(str(raw))
    return warnings


def _log_line(event: LogEvent) -> str:
    detail = json.dumps(event.detail, ensure_ascii=False, default=str)
    return f"- {event.wall_time.isoformat()} sim={event.sim_time_seconds:g} {event.kind} {detail}"


def _sim_days(seconds: float) -> str:
    return _days(seconds / _SIM_DAY)


def _days(value: float) -> str:
    unit = "sim-day" if value == 1 else "sim-days"
    return f"{value:g} {unit}"
