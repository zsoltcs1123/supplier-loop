from pydantic import BaseModel, ConfigDict

from supplier_loop.round_state.models import QuoteLine

_MODEL_CONFIG = ConfigDict(extra="forbid")


class ExtractAttachment(BaseModel):
    model_config = _MODEL_CONFIG

    filename: str
    mime_type: str


class ExtractRequest(BaseModel):
    model_config = _MODEL_CONFIG

    email_id: str
    body: str
    attachments: list[ExtractAttachment] = []


class ExtractResult(BaseModel):
    model_config = _MODEL_CONFIG

    line_items: list[QuoteLine]
    payment_terms: str
    validity_days: int
    grand_total: float
    injection_suspected: bool
