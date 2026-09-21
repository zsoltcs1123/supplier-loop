import pytest

from supplier_loop.mail_kind.classify import MailKind, classify_mail
from supplier_loop.round_state.fingerprint import quote_fingerprint
from supplier_loop.simulator.port import EmailMessage
from tests.unit.sample_traffic import (
    email_from_json,
    load_approver_ruling,
    load_sample_email,
    sample_email_paths,
)

_NEGOTIATION_SAMPLE_IDS = frozenset({"sample-004", "sample-018"})

_KIND_BY_ID: dict[str, MailKind] = {
    "sample-001": "quote",
    "sample-002": "quote",
    "sample-003": "quote",
    "sample-004": "negotiation_reply",
    "sample-005": "question",
    "sample-006": "question",
    "sample-007": "quote",
    "sample-008": "quote",
    "sample-009": "quote",
    "sample-010": "quote",
    "sample-011": "quote",
    "sample-012": "quote",
    "sample-013": "quote",
    "sample-014": "quote",
    "sample-015": "quote",
    "sample-016": "quote",
    "sample-017": "quote",
    "sample-018": "negotiation_reply",
    "sample-019": "quote",
    "sample-020": "quote",
}


@pytest.mark.unit
@pytest.mark.parametrize(
    "email_id,kind",
    list(_KIND_BY_ID.items()),
    ids=list(_KIND_BY_ID),
)
def test_classify_mail_returns_expected_kind_when_sample_traffic_loaded(
    email_id: str, kind: MailKind
) -> None:
    message = load_sample_email(email_id)

    assert classify_mail(message, negotiation_open=email_id in _NEGOTIATION_SAMPLE_IDS) == kind


@pytest.mark.unit
def test_classify_mail_returns_duplicate_when_quote_fingerprint_already_seen() -> None:
    first = load_sample_email("sample-011")
    second = first.model_copy(update={"id": "sample-011-resend"})
    fingerprint = quote_fingerprint(first)
    seen = {fingerprint}

    kind = classify_mail(second, seen_fingerprints=seen, fingerprint=quote_fingerprint(second))

    assert kind == "duplicate"
    assert seen == {fingerprint}


@pytest.mark.unit
def test_classify_mail_returns_quote_when_same_sender_subject_body_differs() -> None:
    first = load_sample_email("sample-011")
    second = load_sample_email("sample-012")
    seen = {quote_fingerprint(first)}

    assert classify_mail(second, seen_fingerprints=seen, fingerprint=quote_fingerprint(second)) == (
        "quote"
    )


@pytest.mark.unit
def test_classify_mail_returns_quote_when_unit_sits_between_qty_and_price() -> None:
    message = EmailMessage(
        id="in-x-total",
        from_address="marta.novak@novaksteel.example",
        to_address="candidate@sim.local",
        subject="Your RFQ RFQ-005: offer",
        sim_time_hours=47.0,
        attachment_ids=[],
        body=(
            "Pricing follows.\n\n"
            "· 100 pcs Brass Fitting 1/2in x 6.18 per pcs, total 618.00\n"
            "· 100 m PVC Pipe 50mm x 4.58 per m, total 458.00\n\n"
            "Payment Net 30 / validity 30 days / total 1076.00 USD\n"
        ),
    )

    assert classify_mail(message) == "quote"


@pytest.mark.unit
def test_classify_mail_returns_negotiation_reply_when_body_is_number_only() -> None:
    message = EmailMessage(
        id="in-number",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Re: Counter-offer for RFQ-001",
        sim_time_hours=4.0,
        attachment_ids=[],
        body="4,200.00",
    )

    assert classify_mail(message, negotiation_open=True) == "negotiation_reply"


@pytest.mark.unit
def test_classify_mail_returns_unknown_when_number_arrives_before_counter_offer() -> None:
    message = EmailMessage(
        id="in-number",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Re: Counter-offer for RFQ-001",
        sim_time_hours=4.0,
        attachment_ids=[],
        body="4,200.00",
    )

    assert classify_mail(message) == "unknown"


@pytest.mark.unit
def test_classify_mail_returns_negotiation_reply_when_supplier_meets_the_total() -> None:
    message = EmailMessage(
        id="in-meet",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Re: pricing discussion, RFQ RFQ-004",
        sim_time_hours=5.0,
        attachment_ids=[],
        body="We can meet you at 4116.00 total — confirmed. Send the PO whenever you're ready.",
    )

    assert classify_mail(message, negotiation_open=True) == "negotiation_reply"


@pytest.mark.unit
def test_classify_mail_returns_unknown_when_acceptance_arrives_before_counter_offer() -> None:
    message = EmailMessage(
        id="in-meet",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Re: pricing discussion, RFQ RFQ-004",
        sim_time_hours=5.0,
        attachment_ids=[],
        body="We can meet you at 4116.00 total — confirmed. Send the PO whenever you're ready.",
    )

    assert classify_mail(message) == "unknown"


@pytest.mark.unit
def test_classify_mail_returns_negotiation_reply_when_waiting_and_phrasing_is_unseen() -> None:
    message = EmailMessage(
        id="in-accept",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Re: Counter-offer for RFQ-001",
        sim_time_hours=6.0,
        attachment_ids=[],
        body="Accepted. Book it on our side.",
    )

    assert classify_mail(message, negotiation_open=True) == "negotiation_reply"


@pytest.mark.unit
def test_classify_mail_returns_unknown_when_body_is_neither_quote_nor_question() -> None:
    message = EmailMessage(
        id="in-chatter",
        from_address="p01@sim.local",
        to_address="buyer@sim.local",
        subject="Re: RFQ RFQ-001",
        sim_time_hours=2.0,
        attachment_ids=[],
        body="Thanks, I am out of the office until Thursday.",
    )

    assert classify_mail(message) == "unknown"


@pytest.mark.unit
def test_classify_mail_returns_unknown_when_quote_is_not_expected() -> None:
    message = load_sample_email("sample-001")

    assert classify_mail(message, quote_open=False) == "unknown"


@pytest.mark.unit
def test_classify_mail_returns_quote_when_attachment_has_no_quote_word() -> None:
    message = EmailMessage(
        id="in-photo",
        from_address="p04@sim.local",
        to_address="buyer@sim.local",
        subject="Re: RFQ-001",
        sim_time_hours=8.0,
        attachment_ids=["shot.png"],
        body="Photo from the yard.",
    )

    assert classify_mail(message) == "quote"


@pytest.mark.unit
def test_classify_mail_returns_quote_when_revision_is_open() -> None:
    message = load_sample_email("sample-001")

    assert classify_mail(message, quote_open=False, revision_open=True) == "quote"


@pytest.mark.unit
def test_classify_mail_returns_approver_ruling_when_from_approver() -> None:
    message = load_approver_ruling()

    assert classify_mail(message) == "approver_ruling"


@pytest.mark.unit
def test_classify_mail_covers_every_sample_json_when_index_is_loaded() -> None:
    paths = sample_email_paths()
    ids = {email_from_json(path).id for path in paths}

    assert ids == set(_KIND_BY_ID)
    assert len(paths) == 20
