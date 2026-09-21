from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

DEV_ROUND_CAP = 20
DEFAULT_BUDGET_PATH = Path("dev-rounds.json")

_MODEL_CONFIG = ConfigDict(extra="forbid")


class DevRoundCall(BaseModel):
    model_config = _MODEL_CONFIG

    wall_time: datetime
    round_id: str


class DevRoundBudget(BaseModel):
    model_config = _MODEL_CONFIG

    cap: int = DEV_ROUND_CAP
    used: int = 0
    remaining: int = DEV_ROUND_CAP
    calls: list[DevRoundCall] = []


def load_budget(path: Path = DEFAULT_BUDGET_PATH) -> DevRoundBudget:
    if not path.exists():
        return _synced(DevRoundBudget())
    return _synced(DevRoundBudget.model_validate_json(path.read_text(encoding="utf-8")))


def save_budget(budget: DevRoundBudget, path: Path = DEFAULT_BUDGET_PATH) -> None:
    synced = _synced(budget)
    path.write_text(synced.model_dump_json(indent=2) + "\n", encoding="utf-8")


def record_dev_round(
    round_id: str,
    path: Path = DEFAULT_BUDGET_PATH,
    *,
    wall_time: datetime | None = None,
) -> DevRoundBudget:
    budget = load_budget(path)
    budget.calls.append(DevRoundCall(wall_time=wall_time or datetime.now(UTC), round_id=round_id))
    save_budget(budget, path)
    return load_budget(path)


def _synced(budget: DevRoundBudget) -> DevRoundBudget:
    used = len(budget.calls)
    return budget.model_copy(update={"used": used, "remaining": max(budget.cap - used, 0)})
