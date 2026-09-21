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


class SentEmail:
    def __init__(self, email_id: str, to: str, subject: str, body: str) -> None:
        self.id = email_id
        self.to = to
        self.subject = subject
        self.body = body


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
        self._assignment = assignment
        self._directory = directory
        self._history = history
        self._clock = clock
        self._inbox = list(inbox)
        self._attachments = attachments
        self._email_bodies: dict[str, str] = {}
        self._sent: list[SentEmail] = []
        self._last_submission: dict[str, SubmitEntry] | None = None
        self._next_sent_id = 1

    def get_assignment(self) -> Assignment:
        return self._assignment

    def get_supplier_directory(self) -> list[SupplierEntry]:
        return self._directory

    def get_price_history(self) -> list[PriceHistoryRow]:
        return self._history

    def list_inbox(self, since_sim_time: float | None = None) -> list[InboxEntry]:
        if since_sim_time is None:
            return list(self._inbox)
        return [entry for entry in self._inbox if entry.sim_time_hours * 3600 > since_sim_time]

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
        return self._attachments[attachment_id]

    def get_sim_clock(self) -> SimClock:
        return self._clock

    def send_email(self, to: str, subject: str, body: str) -> str:
        email_id = f"sent-{self._next_sent_id}"
        self._next_sent_id += 1
        self._sent.append(SentEmail(email_id, to, subject, body))
        return email_id

    def submit_results(self, results: dict[str, SubmitEntry]) -> SubmitEcho:
        self._last_submission = results
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
        self._inbox.append(entry)
        self._email_bodies[entry.id] = body

    def sent_emails(self) -> list[SentEmail]:
        return list(self._sent)

    def last_submission(self) -> dict[str, SubmitEntry] | None:
        return self._last_submission
