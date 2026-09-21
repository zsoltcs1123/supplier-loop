from collections.abc import Sequence

from supplier_loop.extract.port import Extractor
from supplier_loop.extract.schema import ExtractAttachment, ExtractRequest, ExtractResult
from supplier_loop.mail_kind.classify import MailKind, classify_mail
from supplier_loop.quote_pipeline.normalize import description_catalog, normalize_quote_line
from supplier_loop.quote_pipeline.pdf_text import read_pdf_text
from supplier_loop.quote_pipeline.recompute import recomputed_grand_total, recomputed_line_total
from supplier_loop.round_state.fingerprint import quote_fingerprint
from supplier_loop.round_state.models import (
    AsSentQuote,
    DedupRegistry,
    QuoteRecord,
    RfqContext,
    SupplierFacts,
)
from supplier_loop.simulator.port import EmailMessage

_MIME_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
_IMAGE_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


def process_inbound_mail(
    message: EmailMessage,
    *,
    supplier: SupplierFacts,
    rfq: RfqContext,
    dedup: DedupRegistry,
    extractor: Extractor,
    attachments: Sequence[ExtractAttachment] = (),
) -> MailKind:
    fingerprint = quote_fingerprint(message)
    kind = classify_mail(
        message,
        seen_fingerprints=dedup.quote_fingerprints,
        fingerprint=fingerprint,
        quote_open=supplier.quote is None or not supplier.quote.as_sent.line_items,
        negotiation_open=supplier.negotiation_used and not supplier.own_quote_history,
        revision_open=(
            supplier.correction_used
            and supplier.quote is not None
            and supplier.quote.revised_as_sent is None
        ),
    )
    if kind != "quote":
        return kind
    extracted = extractor.extract(_extract_request(message, attachments))
    record = build_quote_record(extracted, rfq)
    if supplier.correction_used and supplier.quote is not None:
        supplier.quote.revised_as_sent = record.as_sent
        supplier.quote.recomputed_total = record.recomputed_total
        supplier.quote.recomputed_grand_total = record.recomputed_grand_total
    else:
        supplier.quote = record
    supplier.injection_suspected = extracted.injection_suspected
    dedup.quote_fingerprints.add(fingerprint)
    return kind


def build_quote_record(extracted: ExtractResult, rfq: RfqContext) -> QuoteRecord:
    catalog = description_catalog(rfq)
    lines = [normalize_quote_line(line, catalog) for line in extracted.line_items]
    line_totals = [recomputed_line_total(line.quantity, line.unit_price) for line in lines]
    grand = recomputed_grand_total(line_totals)
    return QuoteRecord(
        as_sent=AsSentQuote(
            line_items=lines,
            payment_terms=extracted.payment_terms,
            validity_days=extracted.validity_days,
            grand_total=extracted.grand_total,
        ),
        recomputed_total=grand,
        recomputed_grand_total=grand,
    )


def _extract_request(
    message: EmailMessage,
    attachments: Sequence[ExtractAttachment],
) -> ExtractRequest:
    hints = list(attachments) if attachments else _hints_from_names(message.attachment_ids)
    body, vision = _choose_extract_input(message.body, hints)
    return ExtractRequest(email_id=message.id, body=body, attachments=vision)


def _choose_extract_input(
    body: str,
    hints: Sequence[ExtractAttachment],
) -> tuple[str, list[ExtractAttachment]]:
    pdf_texts: list[str] = []
    vision: list[ExtractAttachment] = []
    for item in hints:
        if _is_pdf(item):
            text = read_pdf_text(item.content)
            if text:
                pdf_texts.append(text)
            continue
        if _is_image(item) and item.content:
            vision.append(item)
    if pdf_texts:
        body = body.rstrip() + "\n\n" + "\n\n".join(pdf_texts)
    return body, vision


def _is_pdf(item: ExtractAttachment) -> bool:
    mime = item.mime_type.casefold()
    return mime == "application/pdf" or item.filename.casefold().endswith(".pdf")


def _is_image(item: ExtractAttachment) -> bool:
    mime = item.mime_type.casefold()
    if mime in _IMAGE_MIMES:
        return True
    lowered = item.filename.casefold()
    return lowered.endswith((".png", ".jpg", ".jpeg", ".webp"))


def _hints_from_names(names: Sequence[str]) -> list[ExtractAttachment]:
    return [ExtractAttachment(filename=name, mime_type=_mime_from_name(name)) for name in names]


def _mime_from_name(filename: str) -> str:
    lowered = filename.casefold()
    for suffix, mime in _MIME_BY_SUFFIX.items():
        if lowered.endswith(suffix):
            return mime
    return "application/octet-stream"
