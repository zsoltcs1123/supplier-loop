from datetime import UTC, datetime
from pathlib import Path

import pytest

from supplier_loop.dev_rounds import load_budget, record_dev_round


@pytest.mark.unit
def test_load_budget_returns_full_cap_when_file_missing(tmp_path: Path) -> None:
    budget = load_budget(tmp_path / "dev-rounds.json")

    assert budget.cap == 20
    assert budget.used == 0
    assert budget.remaining == 20
    assert budget.calls == []


@pytest.mark.unit
def test_record_dev_round_appends_call_and_decrements_remaining(tmp_path: Path) -> None:
    path = tmp_path / "dev-rounds.json"
    when = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)

    budget = record_dev_round("dev-1", path, wall_time=when)

    assert budget.used == 1
    assert budget.remaining == 19
    assert budget.calls[0].round_id == "dev-1"
    assert budget.calls[0].wall_time == when
    reloaded = load_budget(path)
    assert reloaded.used == 1
    assert reloaded.remaining == 19
