from typing import TextIO


def emit_progress(
    stream: TextIO,
    *,
    sim_time_seconds: float,
    kind: str,
    subject: str,
) -> None:
    stream.write(f"{sim_time_seconds:.0f}s {kind} {subject}\n")
    stream.flush()
