from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TextIO

from supplier_loop.dev_rounds import DEFAULT_BUDGET_PATH, load_budget, record_dev_round
from supplier_loop.extract.openrouter import DEFAULT_MODEL, OpenRouterExtractor
from supplier_loop.extract.port import Extractor
from supplier_loop.extract.spend import DEFAULT_SPEND_PATH, load_spend
from supplier_loop.operational_log.log import OperationalLog
from supplier_loop.orchestrator.run import run_until_submit
from supplier_loop.propose import write_pack
from supplier_loop.round_state.store import RoundStore, snapshot_world, stored_round_id
from supplier_loop.simulator.mcp import McpSimulator
from supplier_loop.simulator.port import SubmitEntry
from supplier_loop.simulator.session import McpToolSession, ToolCaller, ToolSession

_POLL_SECONDS = 5.0
_MAX_PASSES = 5760
_STATE_ROOT = Path(".artifacts")


def main(argv: list[str] | None = None) -> None:
    """Run ping, a live development round, or dump a proposal pack from disk."""
    _force_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    load_dotenv(Path(".env"))
    if args.command == "pack-propose":
        write_pack(artifacts_root=_STATE_ROOT, out=sys.stdout)
        return
    url, token = require_credentials()
    with McpToolSession(url, token) as session:
        if args.command == "ping":
            ping(session, sys.stdout)
            return
        extractor = build_extractor()
        if args.command == "run-dev":
            run_dev_round(
                session,
                sys.stdout,
                extractor=extractor,
                pause_seconds=args.poll_seconds,
                max_passes=args.max_passes,
            )
            return
        if args.command == "resume-dev":
            continue_dev_round(
                session,
                sys.stdout,
                extractor=extractor,
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
    sub.add_parser(
        "pack-propose",
        help="dump a proposal pack from round files on disk; no MCP, no OpenRouter",
    )
    return parser


def ping(
    session: ToolSession,
    out: TextIO,
    *,
    budget_path: Path = DEFAULT_BUDGET_PATH,
    spend_path: Path = DEFAULT_SPEND_PATH,
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
    spend = load_spend(spend_path)
    out.write(f"llm_spend={spend.used:.4f}/{spend.cap:g} remaining={spend.remaining:.4f}\n")


def run_dev_round(
    session: ToolCaller,
    out: TextIO,
    *,
    extractor: Extractor,
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
        extractor=extractor,
        pause_seconds=pause_seconds,
        max_passes=max_passes,
    )


def continue_dev_round(
    session: ToolCaller,
    out: TextIO,
    *,
    extractor: Extractor,
    store: RoundStore | None = None,
    log: OperationalLog | None = None,
    pause_seconds: float = _POLL_SECONDS,
    max_passes: int = _MAX_PASSES,
) -> dict[str, SubmitEntry]:
    round_store = store or RoundStore(_STATE_ROOT / "round")
    clock = McpSimulator(session).get_sim_clock()
    attached = stored_round_id(round_store) != clock.round_id
    if attached:
        round_store.wipe()
    simulator = McpSimulator(session, sent_log=round_store.root / "sent.json")
    if attached:
        snapshot_world(simulator, round_store)
    out.write(
        f"resume round_id={clock.round_id} mode={clock.mode} "
        f"sim_time_seconds={clock.sim_time_seconds:g}"
        f"{' attach' if attached else ''}\n"
    )
    ops = log or OperationalLog(_STATE_ROOT / "ops.jsonl")
    return _finish_round(
        simulator,
        round_store,
        ops,
        out,
        extractor=extractor,
        pause_seconds=pause_seconds,
        max_passes=max_passes,
    )


def _finish_round(
    simulator: McpSimulator,
    round_store: RoundStore,
    ops: OperationalLog,
    out: TextIO,
    *,
    extractor: Extractor,
    pause_seconds: float,
    max_passes: int,
) -> dict[str, SubmitEntry]:
    payload = run_until_submit(
        simulator,
        round_store,
        extractor,
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


def build_extractor(*, spend_path: Path | None = None) -> OpenRouterExtractor:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise SystemExit("Set OPENROUTER_API_KEY")
    model = os.environ.get("OPENROUTER_MODEL", "").strip() or DEFAULT_MODEL
    return OpenRouterExtractor(
        api_key=key,
        model=model,
        spend_path=spend_path or DEFAULT_SPEND_PATH,
    )


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")
