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
def test_process_inbound_mail_passes_attachment_bytes_when_downloaded() -> None:
    message = load_sample_email("sample-001").model_copy(update={"attachment_ids": ["att_02_0001"]})
    extractor = FixtureExtractor({message.id: _extract_result()})
    attachment = ExtractAttachment(
        filename="Terms_addendum_1.pdf",
        mime_type="application/pdf",
        content=b"%PDF-1.4 fake",
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
