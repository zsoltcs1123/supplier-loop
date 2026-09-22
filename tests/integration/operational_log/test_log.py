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
            round_id="dev-1",
            kind="ingest",
            detail={"email_id": "in-1"},
        )
    )
    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 10, 1, tzinfo=UTC),
            sim_time_seconds=200.0,
            round_id="dev-1",
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
    assert "round_id" in lines[0]


@pytest.mark.integration
def test_log_events_for_round_skips_legacy_lines_without_round_id(tmp_path: Path) -> None:
    path = tmp_path / "ops.jsonl"
    log = OperationalLog(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"wall_time":"2026-09-21T10:00:00Z","sim_time_seconds":1.0,'
        '"kind":"ingest","detail":{"email_id":"old"}}\n',
        encoding="utf-8",
    )
    log.append(
        LogEvent(
            wall_time=datetime(2026, 9, 21, 10, 1, tzinfo=UTC),
            sim_time_seconds=2.0,
            round_id="dev-2",
            kind="ingest",
            detail={"email_id": "new"},
        )
    )

    assert [event.round_id for event in log.events()] == ["dev-2"]
    assert [event.kind for event in log.events_for_round("dev-2")] == ["ingest"]
    assert log.events_for_round("dev-1") == []
