from typing import Literal

from pydantic import BaseModel, ConfigDict

from supplier_loop.simulator.port import (
    Assignment,
    InboxEntry,
    PriceHistoryRow,
    SimClock,
    SupplierEntry,
)

_MODEL_CONFIG = ConfigDict(extra="forbid")

SupplierPhase = Literal[
    "idle",
    "rfq_sent",
    "awaiting_quote",
    "quoted",
    "escalated",
    "done",
]


class QuoteLine(BaseModel):
    model_config = _MODEL_CONFIG

    material_id: str | None
    description: str
    quantity: float
    unit_price: float
    total: float


class AsSentQuote(BaseModel):
    model_config = _MODEL_CONFIG

    line_items: list[QuoteLine]
    payment_terms: str
    validity_days: int
    grand_total: float


class QuoteRecord(BaseModel):
    model_config = _MODEL_CONFIG

    as_sent: AsSentQuote
    recomputed_total: float
    recomputed_grand_total: float
    revised_as_sent: AsSentQuote | None = None


class SupplierFacts(BaseModel):
    model_config = _MODEL_CONFIG

    supplier_id: str
    email: str
    phase: SupplierPhase = "idle"
    outbound_ids: list[str] = []
    quote: QuoteRecord | None = None
    escalation_classes: list[int] = []
    approver_rulings: list[str] = []
    correction_used: bool = False
    reminder_sim_time: float | None = None
    question_answered: bool = False
    own_quote_history: list[AsSentQuote] = []


class DedupRegistry(BaseModel):
    model_config = _MODEL_CONFIG

    email_ids: set[str] = set()
    attachment_ids: set[str] = set()
    quote_fingerprints: set[str] = set()


class RfqContext(BaseModel):
    model_config = _MODEL_CONFIG

    assignment: Assignment
    directory: list[SupplierEntry]
    price_history: list[PriceHistoryRow]
    clock: SimClock
    exam_started: bool = False


class RoundState(BaseModel):
    model_config = _MODEL_CONFIG

    rfq: RfqContext
    suppliers: dict[str, SupplierFacts]
    inbox: list[InboxEntry]
    dedup: DedupRegistry
