import io
from datetime import datetime

import pytest

from supplier_loop.progress import emit_progress, format_sim_clock


@pytest.mark.unit
def test_progress_emit_writes_wall_and_sim_clock_when_called() -> None:
    stream = io.StringIO()

    emit_progress(
        stream,
        sim_time_seconds=7201.2,
        kind="reminder_due",
        subject="p02 reminder_due",
        wall_time=datetime(2026, 9, 21, 16, 9, 12),
    )

    assert stream.getvalue() == "16:09:12  2h 00m 01s  reminder_due  p02 reminder_due\n"


@pytest.mark.unit
def test_progress_emit_colors_kind_when_use_color_is_true() -> None:
    stream = io.StringIO()

    emit_progress(
        stream,
        sim_time_seconds=500.0,
        kind="ingest",
        subject="eml_02_0009 quote",
        wall_time=datetime(2026, 9, 21, 16, 9, 12),
        use_color=True,
    )

    assert stream.getvalue() == ("16:09:12  8m 20s  \033[36mingest\033[0m  eml_02_0009 quote\n")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0.0, "0m 00s"),
        (59.9, "0m 59s"),
        (7201.2, "2h 00m 01s"),
        (273968.0, "3d 04h 06m"),
    ],
)
def test_format_sim_clock_uses_days_hours_minutes(seconds: float, expected: str) -> None:
    assert format_sim_clock(seconds) == expected
