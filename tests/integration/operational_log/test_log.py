from datetime import UTC, datetime
from pathlib import Path

import pytest

from supplier_loop.operational_log.log import LogEvent, OperationalLog


@pytest.mark.integration
def test_log_append_writes_jsonl_without_printing_stdout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "logs" / "operational.jsonl"
    log = OperationalLog(path)

    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 10, 0, tzinfo=UTC),
            sim_time_seconds=100.0,
            kind="ingest",
            detail={"email_id": "in-1"},
        )
    )
    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 10, 1, tzinfo=UTC),
            sim_time_seconds=200.0,
            kind="decision",
            detail={"supplier_id": "p02", "note": "watermark \u2014"},
        )
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    captured = capsys.readouterr()
    assert len(lines) == 2
    assert "watermark \u2014" in lines[1]
    assert captured.out == ""
    assert captured.err == ""
