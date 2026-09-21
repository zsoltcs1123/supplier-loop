from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from supplier_loop.simulator.port import (
    Assignment,
    Attachment,
    EmailMessage,
    InboxEntry,
    PriceHistoryRow,
    SentEmailRecord,
    SimClock,
    SubmitEcho,
    SubmitEntry,
    SupplierEntry,
)
from supplier_loop.simulator.session import ToolCaller
from supplier_loop.simulator.wire import (
    parse_assignment,
    parse_attachment,
    parse_clock,
    parse_directory,
    parse_echo,
    parse_email,
    parse_inbox,
    parse_price_history,
    parse_send_id,
)


class McpSimulator:
    def __init__(self, caller: ToolCaller, *, sent_log: Path | None = None) -> None:
        self._caller = caller
        self._sent_log = sent_log
        self._sent = _load_sent(sent_log)
        self._last_echo: SubmitEcho | None = None

    def get_assignment(self) -> Assignment:
        return parse_assignment(self._caller.call_tool("get_assignment"))

    def get_supplier_directory(self) -> list[SupplierEntry]:
        return parse_directory(self._caller.call_tool("get_supplier_directory"))

    def get_price_history(self) -> list[PriceHistoryRow]:
        return parse_price_history(self._caller.call_tool("get_price_history"))

    def list_inbox(self, since_sim_time: float | None = None) -> list[InboxEntry]:
        arguments: dict[str, object] | None = None
        if since_sim_time is not None:
            arguments = {"since_sim_time": since_sim_time}
        return parse_inbox(self._caller.call_tool("list_inbox", arguments))

    def read_email(self, email_id: str) -> EmailMessage:
        return parse_email(self._caller.call_tool("read_email", {"email_id": email_id}))

    def download_attachment(self, attachment_id: str) -> Attachment:
        return parse_attachment(
            self._caller.call_tool("download_attachment", {"attachment_id": attachment_id})
        )

    def get_sim_clock(self) -> SimClock:
        return parse_clock(self._caller.call_tool("get_sim_clock"))

    def send_email(self, to: str, subject: str, body: str) -> str:
        email_id = parse_send_id(
            self._caller.call_tool("send_email", {"to": to, "subject": subject, "body": body})
        )
        self._sent.append(SentEmailRecord(id=email_id, to=to, subject=subject, body=body))
        _save_sent(self._sent_log, self._sent)
        return email_id

    def list_sent(self) -> list[SentEmailRecord]:
        return [
            SentEmailRecord(id=mail.id, to=mail.to, subject=mail.subject, body=mail.body)
            for mail in self._sent
        ]

    def submit_results(self, results: dict[str, SubmitEntry]) -> SubmitEcho:
        dumped = {supplier_id: entry.model_dump() for supplier_id, entry in results.items()}
        echo = parse_echo(self._caller.call_tool("submit_results", {"results": dumped}))
        self._last_echo = echo
        return echo

    def last_echo(self) -> SubmitEcho | None:
        return self._last_echo

    def request_dev_round(self) -> object:
        return self._caller.call_tool("request_dev_round")


def _load_sent(path: Path | None) -> list[SentEmailRecord]:
    if path is None or not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise TypeError("sent log must be a list")
    return [SentEmailRecord.model_validate(item) for item in raw]


def _save_sent(path: Path | None, sent: list[SentEmailRecord]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps([mail.model_dump() for mail in sent])
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
