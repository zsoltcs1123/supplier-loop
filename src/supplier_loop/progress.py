from __future__ import annotations

import os
from datetime import datetime
from typing import TextIO

_RESET = "\033[0m"
_KIND_COLORS = {
    "poll": "2",
    "ingest": "36",
    "rfq_sent": "34",
    "reminder_due": "33",
    "submit": "32;1",
}


def emit_progress(
    stream: TextIO,
    *,
    sim_time_seconds: float,
    kind: str,
    subject: str,
    wall_time: datetime | None = None,
    use_color: bool | None = None,
) -> None:
    wall = wall_time if wall_time is not None else datetime.now().astimezone()
    kind_text = _color_kind(kind, _color_enabled(stream, use_color))
    stream.write(f"{wall:%H:%M:%S}  {format_sim_clock(sim_time_seconds)}  {kind_text}  {subject}\n")
    stream.flush()


def format_sim_clock(sim_time_seconds: float) -> str:
    total = max(0, int(sim_time_seconds))
    days, rem = divmod(total, 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes, seconds = divmod(rem, 60)
    if days:
        return f"{days}d {hours:02d}h {minutes:02d}m"
    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    return f"{minutes}m {seconds:02d}s"


def _color_enabled(stream: TextIO, override: bool | None) -> bool:
    if override is not None:
        return override
    if "NO_COLOR" in os.environ:
        return False
    checker = getattr(stream, "isatty", None)
    return bool(checker()) if callable(checker) else False


def _color_kind(kind: str, enabled: bool) -> str:
    if not enabled:
        return kind
    code = _KIND_COLORS.get(kind, "1")
    return f"\033[{code}m{kind}{_RESET}"
