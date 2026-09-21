from typing import Protocol

from pydantic import BaseModel, ConfigDict

_MODEL_CONFIG = ConfigDict(extra="forbid")


class BomLine(BaseModel):
    model_config = _MODEL_CONFIG

    material_id: str
    description: str
    unit: str
    quantity: float


class Assignment(BaseModel):
    model_config = _MODEL_CONFIG

    rfq_id: str
    required_payment_terms: str
    required_validity_days: int
    target_price_ceiling_pct: float
    line_items: list[BomLine]
    goal_statement: str
    approver_email: str
    escalation_subject_protocol: str


class SupplierEntry(BaseModel):
    model_config = _MODEL_CONFIG

    supplier_id: str
    email: str
    material_ids: list[str]


class PriceHistoryRow(BaseModel):
    model_config = _MODEL_CONFIG

    supplier_id: str
    material_id: str
    description: str
    unit: str
    last_accepted_unit_price: float


class SimClock(BaseModel):
    model_config = _MODEL_CONFIG

    sim_time_seconds: float
    sim_time_days: float
    round_id: str
    mode: str
    clock_factor: float


class InboxEntry(BaseModel):
    model_config = _MODEL_CONFIG

    id: str
    from_address: str
    to_address: str
    subject: str
    sim_time_hours: float
    attachment_ids: list[str]


class EmailMessage(BaseModel):
    model_config = _MODEL_CONFIG

    id: str
    from_address: str
    to_address: str
    subject: str
    sim_time_hours: float
    attachment_ids: list[str]
    body: str


class Attachment(BaseModel):
    model_config = _MODEL_CONFIG

    id: str
    filename: str
    mime_type: str
    content: bytes


class SubmitLineItem(BaseModel):
    model_config = _MODEL_CONFIG

    material_id: str
    quantity: float
    unit_price: float
    total: float


class SubmitEntry(BaseModel):
    model_config = _MODEL_CONFIG

    line_items: list[SubmitLineItem]
    payment_terms: str
    validity_days: int
    grand_total: float
    action_taken: str
    auto_approved: bool


class SubmitEcho(BaseModel):
    model_config = _MODEL_CONFIG

    warnings: list[str]


class Simulator(Protocol):
    def get_assignment(self) -> Assignment: ...

    def get_supplier_directory(self) -> list[SupplierEntry]: ...

    def get_price_history(self) -> list[PriceHistoryRow]: ...

    def list_inbox(self, since_sim_time: float | None = None) -> list[InboxEntry]: ...

    def read_email(self, email_id: str) -> EmailMessage: ...

    def download_attachment(self, attachment_id: str) -> Attachment: ...

    def get_sim_clock(self) -> SimClock: ...

    def send_email(self, to: str, subject: str, body: str) -> str: ...

    def submit_results(self, results: dict[str, SubmitEntry]) -> SubmitEcho: ...
