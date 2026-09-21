from datetime import UTC, datetime
from pathlib import Path

import pytest

from supplier_loop.extract.spend import SpendCapReached, assert_under_cap, load_spend, record_spend


@pytest.mark.unit
def test_load_spend_returns_full_cap_when_file_missing(tmp_path: Path) -> None:
    ledger = load_spend(tmp_path / "llm-spend.json")

    assert ledger.cap == 100.0
    assert ledger.used == 0.0
    assert ledger.remaining == 100.0
    assert ledger.calls == []


@pytest.mark.unit
def test_record_spend_adds_cost_and_decrements_remaining(tmp_path: Path) -> None:
    path = tmp_path / "llm-spend.json"
    when = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)

    ledger = record_spend(
        model="openai/gpt-4o-mini",
        cost=0.0125,
        prompt_tokens=80,
        completion_tokens=40,
        path=path,
        wall_time=when,
    )

    assert ledger.used == 0.0125
    assert ledger.remaining == 99.9875
    assert ledger.calls[0].model == "openai/gpt-4o-mini"
    reloaded = load_spend(path)
    assert reloaded.used == 0.0125


@pytest.mark.unit
def test_assert_under_cap_raises_when_used_reaches_cap(tmp_path: Path) -> None:
    path = tmp_path / "llm-spend.json"
    record_spend(
        model="openai/gpt-4o-mini",
        cost=100.0,
        prompt_tokens=1,
        completion_tokens=1,
        path=path,
    )

    with pytest.raises(SpendCapReached, match="100"):
        assert_under_cap(path)
