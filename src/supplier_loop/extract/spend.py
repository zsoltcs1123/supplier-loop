from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

SPEND_CAP = 100.0
DEFAULT_SPEND_PATH = Path(".artifacts/llm-spend.json")

_MODEL_CONFIG = ConfigDict(extra="forbid")


class SpendCall(BaseModel):
    model_config = _MODEL_CONFIG

    wall_time: datetime
    model: str
    cost: float
    prompt_tokens: int
    completion_tokens: int


class SpendLedger(BaseModel):
    model_config = _MODEL_CONFIG

    cap: float = SPEND_CAP
    used: float = 0.0
    remaining: float = SPEND_CAP
    calls: list[SpendCall] = []


class SpendCapReached(RuntimeError):
    pass


def load_spend(path: Path = DEFAULT_SPEND_PATH) -> SpendLedger:
    if not path.exists():
        return _synced(SpendLedger())
    return _synced(SpendLedger.model_validate_json(path.read_text(encoding="utf-8")))


def save_spend(ledger: SpendLedger, path: Path = DEFAULT_SPEND_PATH) -> None:
    synced = _synced(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(synced.model_dump_json(indent=2) + "\n", encoding="utf-8")


def record_spend(
    *,
    model: str,
    cost: float,
    prompt_tokens: int,
    completion_tokens: int,
    path: Path = DEFAULT_SPEND_PATH,
    wall_time: datetime | None = None,
) -> SpendLedger:
    ledger = load_spend(path)
    ledger.calls.append(
        SpendCall(
            wall_time=wall_time or datetime.now(UTC),
            model=model,
            cost=cost,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    )
    save_spend(ledger, path)
    return load_spend(path)


def assert_under_cap(path: Path = DEFAULT_SPEND_PATH) -> SpendLedger:
    ledger = load_spend(path)
    if ledger.used >= ledger.cap:
        raise SpendCapReached(f"OpenRouter spend cap reached: {ledger.used:.4f}/{ledger.cap:g}")
    return ledger


def _synced(ledger: SpendLedger) -> SpendLedger:
    used = round(sum(call.cost for call in ledger.calls), 6)
    return ledger.model_copy(update={"used": used, "remaining": max(ledger.cap - used, 0.0)})
