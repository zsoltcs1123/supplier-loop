import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError


class LogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wall_time: datetime
    sim_time_seconds: float
    round_id: str
    kind: str
    detail: dict[str, object]


class OperationalLog:
    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, event: LogEvent) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json())
            handle.write("\n")

    def record(
        self,
        *,
        round_id: str,
        sim_time_seconds: float,
        kind: str,
        detail: dict[str, object],
    ) -> None:
        self.append(
            LogEvent(
                wall_time=datetime.now(UTC),
                sim_time_seconds=sim_time_seconds,
                round_id=round_id,
                kind=kind,
                detail=detail,
            )
        )

    def events(self) -> list[LogEvent]:
        if not self._path.exists():
            return []
        parsed: list[LogEvent] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            event = _parse_event(line)
            if event is not None:
                parsed.append(event)
        return parsed

    def events_for_round(self, round_id: str) -> list[LogEvent]:
        return [event for event in self.events() if event.round_id == round_id]


def _parse_event(line: str) -> LogEvent | None:
    if not line.strip():
        return None
    try:
        return LogEvent.model_validate_json(line)
    except ValidationError:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None
        if "round_id" not in data:
            return None
        raise
