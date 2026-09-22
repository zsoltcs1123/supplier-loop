import json
import os
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from supplier_loop.cli import (
    build_extractor,
    build_parser,
    continue_dev_round,
    load_dotenv,
    ping,
    require_credentials,
)
from supplier_loop.extract.fixture import FixtureExtractor
from supplier_loop.round_state.store import RoundStore


class _PingSession:
    def __init__(self) -> None:
        self.tools = ["get_sim_clock", "request_dev_round"]
        self.clock = {
            "sim_time_seconds": 12.0,
            "sim_time_days": 0.0,
            "round_id": "dev-1",
            "mode": "dev",
            "clock_factor": 60.0,
        }

    def list_tool_names(self) -> list[str]:
        return list(self.tools)

    def call_tool(self, name: str, arguments: dict[str, object] | None = None) -> object:
        if name != "get_sim_clock":
            raise AssertionError(name)
        return self.clock


@pytest.mark.unit
def test_load_dotenv_sets_missing_keys_when_file_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SUPPLIER_LOOP_DOTENV_TEST", raising=False)
    path = tmp_path / ".env"
    path.write_text("SUPPLIER_LOOP_DOTENV_TEST=from-file\n", encoding="utf-8")

    load_dotenv(path)

    assert os.environ["SUPPLIER_LOOP_DOTENV_TEST"] == "from-file"


@pytest.mark.unit
def test_require_credentials_exits_when_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPPLIER_SIM_MCP_URL", "https://example.test/mcp")
    monkeypatch.delenv("SUPPLIER_SIM_TOKEN", raising=False)

    with pytest.raises(SystemExit, match="SUPPLIER_SIM_TOKEN"):
        require_credentials()


@pytest.mark.unit
def test_ping_writes_clock_when_session_returns_tools_and_clock(tmp_path: Path) -> None:
    out = StringIO()

    ping(
        _PingSession(),
        out,
        budget_path=tmp_path / "dev-rounds.json",
        spend_path=tmp_path / "llm-spend.json",
    )

    text = out.getvalue()
    assert "get_sim_clock" in text
    assert "round_id=dev-1" in text
    assert "mode=dev" in text
    assert "clock_factor=60" in text
    assert "dev_rounds=0/20 remaining=20" in text
    assert "llm_spend=0.0000/100 remaining=100.0000" in text


@pytest.mark.unit
def test_parser_omits_start_exam_command() -> None:
    help_text = build_parser().format_help()

    assert "start_exam" not in help_text
    assert "start-exam" not in help_text
    assert "run-dev" in help_text
    assert "resume-dev" in help_text
    assert "pack-propose" in help_text


@pytest.mark.unit
def test_parser_defaults_poll_and_max_passes_when_run_dev() -> None:
    args = build_parser().parse_args(["run-dev"])

    assert args.poll_seconds == 5.0
    assert args.max_passes == 5760


@pytest.mark.unit
def test_parser_accepts_poll_and_max_passes_when_resume_dev() -> None:
    args = build_parser().parse_args(["resume-dev", "--poll-seconds", "2.5", "--max-passes", "12"])

    assert args.poll_seconds == 2.5
    assert args.max_passes == 12


@pytest.mark.unit
def test_build_extractor_exits_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    with pytest.raises(SystemExit, match="OPENROUTER_API_KEY"):
        build_extractor()


class _ResumeClockSession:
    def __init__(self, *, round_id: str = "exam-1") -> None:
        self.calls: list[str] = []
        self.round_id = round_id

    def list_tool_names(self) -> list[str]:
        return ["get_sim_clock"]

    def call_tool(self, name: str, arguments: dict[str, object] | None = None) -> object:
        self.calls.append(name)
        if name == "get_sim_clock":
            return {
                "sim_time_seconds": 100.0,
                "sim_time_days": 0.0,
                "round_id": self.round_id,
                "mode": "exam",
                "clock_factor": 60.0,
            }
        raise AssertionError(name)


@pytest.mark.unit
def test_continue_dev_round_attaches_when_round_id_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    round_root = tmp_path / "round"
    round_root.mkdir()
    (round_root / "round.json").write_text(
        json.dumps(
            {
                "rfq": {
                    "assignment": {
                        "rfq_id": "RFQ-old",
                        "required_payment_terms": "Net 30",
                        "required_validity_days": 14,
                        "target_price_ceiling_pct": 5.0,
                        "line_items": [],
                        "goal_statement": "old",
                        "approver_email": "approver@sim.local",
                        "escalation_subject_protocol": "[REF:<supplier_id>]",
                    },
                    "directory": [],
                    "price_history": [],
                    "clock": {
                        "sim_time_seconds": 1.0,
                        "sim_time_days": 0.0,
                        "round_id": "dev-old",
                        "mode": "dev",
                        "clock_factor": 60.0,
                    },
                },
                "suppliers": {},
                "inbox": [],
                "dedup": {"email_ids": [], "quote_fingerprints": []},
            }
        ),
        encoding="utf-8",
    )
    session = _ResumeClockSession(round_id="exam-1")
    snapshot_called = False

    def fake_snapshot(simulator: object, store: RoundStore) -> None:
        nonlocal snapshot_called
        snapshot_called = True

    monkeypatch.setattr("supplier_loop.cli.snapshot_world", fake_snapshot)
    monkeypatch.setattr("supplier_loop.cli._finish_round", lambda *args, **kwargs: {})

    out = StringIO()
    continue_dev_round(
        session,
        out,
        extractor=FixtureExtractor({}),
        store=RoundStore(round_root),
        log=MagicMock(),
        pause_seconds=0.0,
        max_passes=1,
    )

    assert "request_dev_round" not in session.calls
    assert "start_exam" not in session.calls
    assert "attach" in out.getvalue()
    assert snapshot_called
    assert not (round_root / "round.json").exists()


@pytest.mark.unit
def test_continue_dev_round_resumes_without_attach_when_round_id_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    round_root = tmp_path / "round"
    round_root.mkdir()
    (round_root / "round.json").write_text(
        json.dumps(
            {
                "rfq": {
                    "assignment": {
                        "rfq_id": "RFQ-001",
                        "required_payment_terms": "Net 30",
                        "required_validity_days": 14,
                        "target_price_ceiling_pct": 5.0,
                        "line_items": [],
                        "goal_statement": "goal",
                        "approver_email": "approver@sim.local",
                        "escalation_subject_protocol": "[REF:<supplier_id>]",
                    },
                    "directory": [],
                    "price_history": [],
                    "clock": {
                        "sim_time_seconds": 1.0,
                        "sim_time_days": 0.0,
                        "round_id": "exam-1",
                        "mode": "exam",
                        "clock_factor": 60.0,
                    },
                },
                "suppliers": {},
                "inbox": [],
                "dedup": {"email_ids": [], "quote_fingerprints": []},
            }
        ),
        encoding="utf-8",
    )
    session = _ResumeClockSession(round_id="exam-1")
    snapshot_called = False

    def fake_snapshot(simulator: object, store: RoundStore) -> None:
        nonlocal snapshot_called
        snapshot_called = True

    monkeypatch.setattr("supplier_loop.cli.snapshot_world", fake_snapshot)
    monkeypatch.setattr("supplier_loop.cli._finish_round", lambda *args, **kwargs: {})

    out = StringIO()
    continue_dev_round(
        session,
        out,
        extractor=FixtureExtractor({}),
        store=RoundStore(round_root),
        log=MagicMock(),
        pause_seconds=0.0,
        max_passes=1,
    )

    assert "attach" not in out.getvalue()
    assert not snapshot_called
    assert (round_root / "round.json").exists()


@pytest.mark.unit
def test_build_extractor_uses_default_model_when_env_blank(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("OPENROUTER_MODEL", "")

    extractor = build_extractor(spend_path=tmp_path / "llm-spend.json")

    assert extractor.model == "google/gemini-2.5-pro"
