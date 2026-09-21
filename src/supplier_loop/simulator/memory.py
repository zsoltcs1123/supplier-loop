from dataclasses import dataclass, replace

from supplier_loop.simulator.port import (
    Assignment,
    Attachment,
    EmailMessage,
    InboxEntry,
    PriceHistoryRow,
    SimClock,
    SubmitEcho,
    SubmitEntry,
    SupplierEntry,
)


@dataclass
class SentEmail:
    id: str
    to: str
    subject: str
    body: str


class InMemorySimulator:
    def __init__(
        self,
        assignment: Assignment,
        directory: list[SupplierEntry],
        history: list[PriceHistoryRow],
        clock: SimClock,
        inbox: list[InboxEntry],
        attachments: dict[str, Attachment],
    ) -> None:
        self._assignment = assignment.model_copy(deep=True)
        self._directory = [entry.model_copy(deep=True) for entry in directory]
        self._history = [row.model_copy(deep=True) for row in history]
        self._clock = clock.model_copy(deep=True)
        self._inbox = [entry.model_copy(deep=True) for entry in inbox]
        self._attachments = {
            attachment_id: attachment.model_copy(deep=True)
            for attachment_id, attachment in attachments.items()
        }
        self._email_bodies: dict[str, str] = {}
        self._sent: list[SentEmail] = []
        self._last_submission: dict[str, SubmitEntry] | None = None
        self._next_sent_id = 1

    def get_assignment(self) -> Assignment:
        return self._assignment.model_copy(deep=True)

    def get_supplier_directory(self) -> list[SupplierEntry]:
        return [entry.model_copy(deep=True) for entry in self._directory]

    def get_price_history(self) -> list[PriceHistoryRow]:
        return [row.model_copy(deep=True) for row in self._history]

    def list_inbox(self, since_sim_time: float | None = None) -> list[InboxEntry]:
        entries = self._inbox
        if since_sim_time is not None:
            entries = [entry for entry in entries if entry.sim_time_hours * 3600 > since_sim_time]
        return [entry.model_copy(deep=True) for entry in entries]

    def read_email(self, email_id: str) -> EmailMessage:
        for entry in self._inbox:
            if entry.id == email_id:
                body = self._email_bodies.get(email_id, "")
                return EmailMessage(
                    id=entry.id,
                    from_address=entry.from_address,
                    to_address=entry.to_address,
                    subject=entry.subject,
                    sim_time_hours=entry.sim_time_hours,
                    attachment_ids=entry.attachment_ids,
                    body=body,
                )
        raise KeyError(email_id)

    def download_attachment(self, attachment_id: str) -> Attachment:
        if attachment_id not in self._attachments:
            raise KeyError(attachment_id)
        return self._attachments[attachment_id].model_copy(deep=True)

    def get_sim_clock(self) -> SimClock:
        return self._clock.model_copy(deep=True)

    def send_email(self, to: str, subject: str, body: str) -> str:
        email_id = f"sent-{self._next_sent_id}"
        self._next_sent_id += 1
        self._sent.append(SentEmail(id=email_id, to=to, subject=subject, body=body))
        return email_id

    def submit_results(self, results: dict[str, SubmitEntry]) -> SubmitEcho:
        self._last_submission = _copy_submit_results(results)
        return SubmitEcho(warnings=[])

    def advance_clock(self, sim_time_seconds: float, sim_time_days: float) -> None:
        self._clock = SimClock(
            sim_time_seconds=sim_time_seconds,
            sim_time_days=sim_time_days,
            round_id=self._clock.round_id,
            mode=self._clock.mode,
            clock_factor=self._clock.clock_factor,
        )

    def push_inbox(self, entry: InboxEntry, body: str = "") -> None:
        self._inbox.append(entry.model_copy(deep=True))
        self._email_bodies[entry.id] = body

    def sent_emails(self) -> list[SentEmail]:
        return [replace(email) for email in self._sent]

    def last_submission(self) -> dict[str, SubmitEntry] | None:
        if self._last_submission is None:
            return None
        return _copy_submit_results(self._last_submission)


def _copy_submit_results(results: dict[str, SubmitEntry]) -> dict[str, SubmitEntry]:
    return {supplier_id: entry.model_copy(deep=True) for supplier_id, entry in results.items()}
