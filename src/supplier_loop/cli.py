from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TextIO

from supplier_loop.dev_rounds import DEFAULT_BUDGET_PATH, load_budget, record_dev_round
from supplier_loop.extract.crude import CrudeExtractor
from supplier_loop.operational_log.log import OperationalLog
from supplier_loop.orchestrator.run import run_until_submit
from supplier_loop.round_state.store import RoundStore, snapshot_world
from supplier_loop.simulator.mcp import McpSimulator
from supplier_loop.simulator.port import SubmitEntry
from supplier_loop.simulator.session import McpToolSession, ToolCaller, ToolSession

_POLL_SECONDS = 5.0
_MAX_PASSES = 2880
_STATE_ROOT = Path(".artifacts")


def main(argv: list[str] | None = None) -> None:
    """Run ping or a live development round against the simulator."""
    parser = build_parser()
    args = parser.parse_args(argv)
    load_dotenv(Path(".env"))
    url, token = require_credentials()
    with McpToolSession(url, token) as session:
        if args.command == "ping":
            ping(session, sys.stdout)
            return
        if args.command == "run-dev":
            run_dev_round(
                session,
                sys.stdout,
                pause_seconds=args.poll_seconds,
                max_passes=args.max_passes,
            )
            return
        if args.command == "resume-dev":
            continue_dev_round(
                session,
                sys.stdout,
                pause_seconds=args.poll_seconds,
                max_passes=args.max_passes,
            )
            return
        raise AssertionError(args.command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="supplier-loop")
    loop_opts = argparse.ArgumentParser(add_help=False)
    loop_opts.add_argument(
        "--poll-seconds",
        type=float,
        default=_POLL_SECONDS,
        help="seconds to wait between passes",
    )
    loop_opts.add_argument(
        "--max-passes",
        type=int,
        default=_MAX_PASSES,
        help="stop after this many poll passes",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ping", help="verify MCP connectivity without starting a round")
    sub.add_parser(
        "run-dev",
        parents=[loop_opts],
        help="call request_dev_round and run until submit_results",
    )
    sub.add_parser(
        "resume-dev",
        parents=[loop_opts],
        help="continue the current round until submit_results",
    )
    return parser


def ping(
    session: ToolSession,
    out: TextIO,
    *,
    budget_path: Path = DEFAULT_BUDGET_PATH,
) -> None:
    names = session.list_tool_names()
    out.write("tools: " + ", ".join(names) + "\n")
    clock = McpSimulator(session).get_sim_clock()
    out.write(
        f"round_id={clock.round_id} mode={clock.mode} "
        f"sim_time_seconds={clock.sim_time_seconds:g} clock_factor={clock.clock_factor:g}\n"
    )
    budget = load_budget(budget_path)
    out.write(f"dev_rounds={budget.used}/{budget.cap} remaining={budget.remaining}\n")


def run_dev_round(
    session: ToolCaller,
    out: TextIO,
    *,
    store: RoundStore | None = None,
    log: OperationalLog | None = None,
    pause_seconds: float = _POLL_SECONDS,
    max_passes: int = _MAX_PASSES,
    budget_path: Path = DEFAULT_BUDGET_PATH,
) -> dict[str, SubmitEntry]:
    round_store = store or RoundStore(_STATE_ROOT / "round")
    round_store.wipe()
    simulator = McpSimulator(session, sent_log=round_store.root / "sent.json")
    simulator.request_dev_round()
    budget = record_dev_round(simulator.get_sim_clock().round_id, budget_path)
    out.write(f"dev_rounds={budget.used}/{budget.cap} remaining={budget.remaining}\n")
    snapshot_world(simulator, round_store)
    ops = log or OperationalLog(_STATE_ROOT / "ops.jsonl")
    return _finish_round(
        simulator,
        round_store,
        ops,
        out,
        pause_seconds=pause_seconds,
        max_passes=max_passes,
    )


def continue_dev_round(
    session: ToolCaller,
    out: TextIO,
    *,
    store: RoundStore | None = None,
    log: OperationalLog | None = None,
    pause_seconds: float = _POLL_SECONDS,
    max_passes: int = _MAX_PASSES,
) -> dict[str, SubmitEntry]:
    round_store = store or RoundStore(_STATE_ROOT / "round")
    simulator = McpSimulator(session, sent_log=round_store.root / "sent.json")
    clock = simulator.get_sim_clock()
    out.write(
        f"resume round_id={clock.round_id} mode={clock.mode} "
        f"sim_time_seconds={clock.sim_time_seconds:g}\n"
    )
    ops = log or OperationalLog(_STATE_ROOT / "ops.jsonl")
    return _finish_round(
        simulator,
        round_store,
        ops,
        out,
        pause_seconds=pause_seconds,
        max_passes=max_passes,
    )


def _finish_round(
    simulator: McpSimulator,
    round_store: RoundStore,
    ops: OperationalLog,
    out: TextIO,
    *,
    pause_seconds: float,
    max_passes: int,
) -> dict[str, SubmitEntry]:
    payload = run_until_submit(
        simulator,
        round_store,
        CrudeExtractor(),
        ops,
        progress=out,
        pause_seconds=pause_seconds,
        max_passes=max_passes,
    )
    dumped = {supplier_id: entry.model_dump() for supplier_id, entry in payload.items()}
    out.write(json.dumps(dumped, indent=2) + "\n")
    echo = simulator.last_echo()
    warnings = echo.warnings if echo is not None else []
    out.write("warnings: " + json.dumps(warnings) + "\n")
    return payload


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), _unquote(value.strip()))


def require_credentials() -> tuple[str, str]:
    url = os.environ.get("SUPPLIER_SIM_MCP_URL", "").strip()
    token = os.environ.get("SUPPLIER_SIM_TOKEN", "").strip()
    if not url or not token:
        raise SystemExit("Set SUPPLIER_SIM_MCP_URL and SUPPLIER_SIM_TOKEN")
    return url, token


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
