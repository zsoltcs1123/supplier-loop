from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class LogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wall_time: datetime
    sim_time_seconds: float
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
