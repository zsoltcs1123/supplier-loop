import pytest

from supplier_loop.extract.fixture import FixtureExtractor
from supplier_loop.extract.schema import ExtractAttachment, ExtractResult
from supplier_loop.quote_pipeline.pipeline import process_inbound_mail
from supplier_loop.round_state.models import (
    AsSentQuote,
    DedupRegistry,
    QuoteLine,
    QuoteRecord,
    RfqContext,
    SupplierFacts,
)
from supplier_loop.simulator.port import Assignment, BomLine, EmailMessage, SimClock
from tests.unit.quote_pipeline.test_pdf_text import pdf_with_text
from tests.unit.sample_traffic import load_approver_ruling, load_sample_email


def _rfq() -> RfqContext:
    return RfqContext(
        assignment=Assignment(
            rfq_id="RFQ-001",
            required_payment_terms="Net 30",
            required_validity_days=14,
            target_price_ceiling_pct=5.0,
            line_items=[
                BomLine(
                    material_id="STL-BEAM-200",
                    description="Steel I-Beam 200mm",
                    unit="m",
                    quantity=100.0,
                )
            ],
            goal_statement="Cover the BOM",
            approver_email="approver@sim.local",
            escalation_subject_protocol="[REF:<supplier_id>]",
        ),
        directory=[],
        price_history=[],
        clock=SimClock(
            sim_time_seconds=0.0,
            sim_time_days=0.0,
            round_id="dev-1",
            mode="development",
            clock_factor=60.0,
        ),
    )


def _supplier(email: str = "marta.novak@novaksteel.example") -> SupplierFacts:
    return SupplierFacts(supplier_id="p01", email=email)


def _extract_result() -> ExtractResult:
    return ExtractResult(
        line_items=[
            QuoteLine(
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                quantity=50.0,
                unit_price=42.29,
                total=1.0,
            )
        ],
        payment_terms="Net 30",
        validity_days=30,
        grand_total=99.0,
        injection_suspected=False,
    )


def _quote_record() -> QuoteRecord:
    return QuoteRecord(
        as_sent=AsSentQuote(
            line_items=[
                QuoteLine(
                    material_id="STL-BEAM-200",
                    description="Steel I-Beam 200mm",
                    quantity=50.0,
                    unit_price=42.29,
                    total=2114.5,
                )
            ],
            payment_terms="Net 30",
            validity_days=30,
            grand_total=2114.5,
        ),
        recomputed_total=2114.5,
        recomputed_grand_total=2114.5,
    )


@pytest.mark.unit
def test_process_inbound_mail_writes_quote_record_when_kind_is_quote() -> None:
    message = load_sample_email("sample-001")
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier()
    dedup = DedupRegistry()

    kind = process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )

    assert kind == "quote"
    assert [request.email_id for request in extractor.requests] == [message.id]
    assert extractor.requests[0].body == message.body
    assert supplier.quote is not None
    assert supplier.quote.as_sent.grand_total == 99.0
    assert supplier.quote.recomputed_grand_total == 2114.5
    assert supplier.quote.as_sent.line_items[0].total == 1.0
    assert supplier.quote.as_sent.payment_terms == "Net 30"
    assert supplier.quote.as_sent.validity_days == 30


@pytest.mark.unit
def test_process_inbound_mail_does_not_call_extract_when_kind_is_question() -> None:
    message = load_sample_email("sample-005")
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier()
    dedup = DedupRegistry()

    kind = process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )

    assert kind == "question"
    assert extractor.requests == []
    assert supplier.quote is None


@pytest.mark.unit
def test_process_inbound_mail_does_not_call_extract_when_negotiation_reply() -> None:
    message = load_sample_email("sample-004")
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier()
    supplier.quote = _quote_record()
    supplier.negotiation_used = True
    before = [line.model_copy(deep=True) for line in supplier.quote.as_sent.line_items]
    dedup = DedupRegistry()

    kind = process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )

    assert kind == "negotiation_reply"
    assert extractor.requests == []
    assert supplier.quote is not None
    assert supplier.quote.as_sent.line_items == before


@pytest.mark.unit
def test_process_inbound_mail_leaves_as_sent_line_items_when_negotiation_reply() -> None:
    message = load_sample_email("sample-018")
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier(email="fatima.alsayed@alsayedtrading.example")
    original = _quote_record()
    supplier.quote = original
    supplier.negotiation_used = True
    dedup = DedupRegistry()

    process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )

    assert supplier.quote is original
    assert supplier.quote.as_sent.line_items[0].unit_price == 42.29
    assert extractor.requests == []


@pytest.mark.unit
def test_process_inbound_mail_does_not_call_extract_when_duplicate() -> None:
    first = load_sample_email("sample-011")
    second = first.model_copy(update={"id": "sample-011-resend"})
    extractor = FixtureExtractor({first.id: _extract_result(), second.id: _extract_result()})
    supplier = _supplier(email="y.tanaka@tanakaprecision.example")
    dedup = DedupRegistry()

    first_kind = process_inbound_mail(
        first,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )
    first_quote = supplier.quote
    second_kind = process_inbound_mail(
        second,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )

    assert first_kind == "quote"
    assert second_kind == "duplicate"
    assert [request.email_id for request in extractor.requests] == [first.id]
    assert supplier.quote is first_quote
    assert first_quote is not None
    assert first_quote.as_sent.line_items[0].quantity == 50.0


@pytest.mark.unit
def test_process_inbound_mail_does_not_call_extract_when_approver_ruling() -> None:
    message = load_approver_ruling()
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier()
    supplier.quote = _quote_record()
    before = supplier.quote
    dedup = DedupRegistry()

    kind = process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )

    assert kind == "approver_ruling"
    assert extractor.requests == []
    assert supplier.quote is before


@pytest.mark.unit
def test_process_inbound_mail_does_not_call_extract_when_number_only_reply() -> None:
    message = EmailMessage(
        id="in-number",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Re: Counter-offer for RFQ-001",
        sim_time_hours=4.0,
        attachment_ids=[],
        body="4,200.00",
    )
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier()
    supplier.quote = _quote_record()
    supplier.negotiation_used = True
    before = [line.model_copy(deep=True) for line in supplier.quote.as_sent.line_items]

    kind = process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=DedupRegistry(),
        extractor=extractor,
    )

    assert kind == "negotiation_reply"
    assert extractor.requests == []
    assert supplier.quote.as_sent.line_items == before


@pytest.mark.unit
def test_process_inbound_mail_inlines_pdf_text_and_drops_pdf_bytes() -> None:
    message = load_sample_email("sample-001").model_copy(update={"attachment_ids": ["att_pdf"]})
    extractor = FixtureExtractor({message.id: _extract_result()})
    attachment = ExtractAttachment(
        filename="tanaka-offer.pdf",
        mime_type="application/pdf",
        content=pdf_with_text("qty 50 Steel I-Beam 200mm 42.29 USD\nNet 30"),
    )

    process_inbound_mail(
        message,
        supplier=_supplier(),
        rfq=_rfq(),
        dedup=DedupRegistry(),
        extractor=extractor,
        attachments=[attachment],
    )

    request = extractor.requests[0]
    assert "qty 50 Steel I-Beam 200mm 42.29 USD" in request.body
    assert request.attachments == []


@pytest.mark.unit
def test_process_inbound_mail_keeps_photo_bytes_for_vision() -> None:
    message = load_sample_email("sample-001").model_copy(update={"attachment_ids": ["att_png"]})
    extractor = FixtureExtractor({message.id: _extract_result()})
    attachment = ExtractAttachment(
        filename="quote.png",
        mime_type="image/png",
        content=b"\x89PNG\r\n",
    )

    process_inbound_mail(
        message,
        supplier=_supplier(),
        rfq=_rfq(),
        dedup=DedupRegistry(),
        extractor=extractor,
        attachments=[attachment],
    )

    assert extractor.requests[0].attachments == [attachment]


@pytest.mark.unit
def test_process_inbound_mail_does_not_extract_when_mail_is_unknown() -> None:
    message = EmailMessage(
        id="in-chatter",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Re: RFQ RFQ-001",
        sim_time_hours=2.0,
        attachment_ids=[],
        body="Thanks, I am out of the office until Thursday.",
    )
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier()

    kind = process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=DedupRegistry(),
        extractor=extractor,
    )

    assert kind == "unknown"
    assert extractor.requests == []
    assert supplier.quote is None
    assert supplier.phase == "idle"


@pytest.mark.unit
def test_process_inbound_mail_keeps_stored_quote_when_a_later_document_arrives() -> None:
    first = load_sample_email("sample-011")
    second = load_sample_email("sample-012")
    extractor = FixtureExtractor({first.id: _extract_result(), second.id: _extract_result()})
    supplier = _supplier(email="y.tanaka@tanakaprecision.example")
    dedup = DedupRegistry()

    process_inbound_mail(
        first,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )
    stored = supplier.quote
    kind = process_inbound_mail(
        second,
        supplier=supplier,
        rfq=_rfq(),
        dedup=dedup,
        extractor=extractor,
    )

    assert kind == "unknown"
    assert supplier.quote is stored
    assert [request.email_id for request in extractor.requests] == [first.id]


@pytest.mark.unit
def test_process_inbound_mail_extracts_again_when_stored_quote_has_no_lines() -> None:
    message = load_sample_email("sample-001")
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier()
    supplier.quote = _quote_record()
    supplier.quote.as_sent.line_items = []

    kind = process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=DedupRegistry(),
        extractor=extractor,
    )

    assert kind == "quote"
    assert extractor.requests
    assert supplier.quote is not None
    assert supplier.quote.as_sent.line_items[0].unit_price == 42.29


@pytest.mark.unit
def test_process_inbound_mail_writes_revised_quote_when_correction_is_open() -> None:
    message = load_sample_email("sample-012")
    extractor = FixtureExtractor({message.id: _extract_result()})
    supplier = _supplier(email="y.tanaka@tanakaprecision.example")
    supplier.quote = _quote_record()
    supplier.correction_used = True
    original_lines = [line.model_copy(deep=True) for line in supplier.quote.as_sent.line_items]

    kind = process_inbound_mail(
        message,
        supplier=supplier,
        rfq=_rfq(),
        dedup=DedupRegistry(),
        extractor=extractor,
    )

    assert kind == "quote"
    assert supplier.quote is not None
    assert supplier.quote.as_sent.line_items == original_lines
    assert supplier.quote.revised_as_sent is not None
    assert supplier.quote.revised_as_sent.grand_total == 99.0
