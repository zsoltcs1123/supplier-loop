import io

import pytest

from supplier_loop.progress import emit_progress


@pytest.mark.unit
def test_progress_emit_writes_one_line_when_called() -> None:
    stream = io.StringIO()

    emit_progress(
        stream,
        sim_time_seconds=7201.2,
        kind="reminder_due",
        subject="p02 reminder_due",
    )

    assert stream.getvalue() == "7201s reminder_due p02 reminder_due\n"
