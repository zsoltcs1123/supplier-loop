import pytest

from supplier_loop.simulator.memory import InMemorySimulator
from supplier_loop.simulator.port import (
    Assignment,
    Attachment,
    BomLine,
    InboxEntry,
    PriceHistoryRow,
    SimClock,
    SubmitEntry,
    SubmitLineItem,
    SupplierEntry,
)


def _simulator(
    inbox: list[InboxEntry] | None = None,
    attachments: dict[str, Attachment] | None = None,
) -> InMemorySimulator:
    return InMemorySimulator(
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
        directory=[
            SupplierEntry(
                supplier_id="p01",
                email="p01@sim.local",
                material_ids=["STL-BEAM-200"],
            ),
            SupplierEntry(
                supplier_id="p02",
                email="p02@sim.local",
                material_ids=["STL-BEAM-200"],
            ),
        ],
        history=[
            PriceHistoryRow(
                supplier_id="p01",
                material_id="STL-BEAM-200",
                description="Steel I-Beam 200mm",
                unit="m",
                last_accepted_unit_price=42.0,
            )
        ],
        clock=SimClock(
            sim_time_seconds=7200.0,
            sim_time_days=0.083,
            round_id="dev-1",
            mode="development",
            clock_factor=60.0,
        ),
        inbox=inbox or [],
        attachments=attachments or {},
    )


@pytest.mark.unit
def test_memory_list_inbox_filters_by_since_sim_time_when_entries_span_hours() -> None:
    simulator = _simulator(
        inbox=[
            InboxEntry(
                id="in-1",
                from_address="p01@sim.local",
                to_address="buyer@sim.local",
                subject="Quote",
                sim_time_hours=1.0,
                attachment_ids=[],
            ),
            InboxEntry(
                id="in-2",
                from_address="p02@sim.local",
                to_address="buyer@sim.local",
                subject="Later quote",
                sim_time_hours=3.0,
                attachment_ids=[],
            ),
        ]
    )

    filtered = simulator.list_inbox(since_sim_time=7200.0)

    assert [entry.id for entry in filtered] == ["in-2"]


@pytest.mark.unit
def test_memory_read_email_returns_body_when_message_exists() -> None:
    simulator = _simulator()
    simulator.push_inbox(
        InboxEntry(
            id="in-1",
            from_address="p01@sim.local",
            to_address="buyer@sim.local",
            subject="Quote",
            sim_time_hours=1.0,
            attachment_ids=[],
        ),
        body="watermark \u2014 offer",
    )

    message = simulator.read_email("in-1")

    assert message.body == "watermark \u2014 offer"
    assert message.from_address == "p01@sim.local"


@pytest.mark.unit
def test_memory_download_attachment_returns_bytes_when_present() -> None:
    attachment = Attachment(
        id="att-1",
        filename="quote.pdf",
        mime_type="application/pdf",
        content=b"%PDF-1.4",
    )
    simulator = _simulator(attachments={"att-1": attachment})

    downloaded = simulator.download_attachment("att-1")

    assert downloaded.content == b"%PDF-1.4"


@pytest.mark.unit
def test_memory_send_email_records_outbound_when_called() -> None:
    simulator = _simulator()

    email_id = simulator.send_email("p01@sim.local", "RFQ", "Please quote")

    sent = simulator.sent_emails()
    assert email_id == "sent-1"
    assert len(sent) == 1
    assert sent[0].to == "p01@sim.local"
    assert sent[0].subject == "RFQ"


@pytest.mark.unit
def test_memory_submit_results_stores_payload_when_called() -> None:
    simulator = _simulator()
    payload = {
        "p01": SubmitEntry(
            line_items=[
                SubmitLineItem(
                    material_id="STL-BEAM-200",
                    quantity=100.0,
                    unit_price=40.0,
                    total=4000.0,
                )
            ],
            payment_terms="Net 30",
            validity_days=14,
            grand_total=4000.0,
            action_taken="extract",
            auto_approved=True,
        )
    }

    echo = simulator.submit_results(payload)

    assert echo.warnings == []
    assert simulator.last_submission() == payload
