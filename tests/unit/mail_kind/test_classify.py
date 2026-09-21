import pytest

from supplier_loop.mail_kind.classify import MailKind, classify_mail
from supplier_loop.round_state.fingerprint import quote_fingerprint
from tests.unit.sample_traffic import (
    email_from_json,
    load_approver_ruling,
    load_sample_email,
    sample_email_paths,
)

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

_QUESTION_IDS = ("sample-005", "sample-006")
_NEGOTIATION_IDS = ("sample-004", "sample-018")
_INLINE_QUOTE_IDS = ("sample-001", "sample-002", "sample-003")
_PASTED_TABLE_IDS = ("sample-007", "sample-008", "sample-009", "sample-010")
_PDF_QUOTE_IDS = ("sample-011", "sample-013", "sample-014", "sample-015")
_PHOTO_QUOTE_IDS = ("sample-016", "sample-017", "sample-019", "sample-020")


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

    assert classify_mail(message) == kind


@pytest.mark.unit
@pytest.mark.parametrize("email_id", _QUESTION_IDS)
def test_classify_mail_returns_question_when_body_has_no_quote_table(email_id: str) -> None:
    message = load_sample_email(email_id)

    assert classify_mail(message) == "question"


@pytest.mark.unit
@pytest.mark.parametrize("email_id", _NEGOTIATION_IDS)
def test_classify_mail_returns_negotiation_reply_when_thread_has_no_table(
    email_id: str,
) -> None:
    message = load_sample_email(email_id)

    assert classify_mail(message) == "negotiation_reply"


@pytest.mark.unit
@pytest.mark.parametrize("email_id", _INLINE_QUOTE_IDS)
def test_classify_mail_returns_quote_when_lines_are_inline(email_id: str) -> None:
    message = load_sample_email(email_id)

    assert classify_mail(message) == "quote"


@pytest.mark.unit
@pytest.mark.parametrize("email_id", _PASTED_TABLE_IDS)
def test_classify_mail_returns_quote_when_table_is_pasted(email_id: str) -> None:
    message = load_sample_email(email_id)

    assert classify_mail(message) == "quote"


@pytest.mark.unit
@pytest.mark.parametrize("email_id", _PDF_QUOTE_IDS)
def test_classify_mail_returns_quote_when_pdf_is_attached(email_id: str) -> None:
    message = load_sample_email(email_id)

    assert classify_mail(message) == "quote"


@pytest.mark.unit
@pytest.mark.parametrize("email_id", _PHOTO_QUOTE_IDS)
def test_classify_mail_returns_quote_when_photo_is_attached(email_id: str) -> None:
    message = load_sample_email(email_id)

    assert classify_mail(message) == "quote"


@pytest.mark.unit
def test_classify_mail_returns_duplicate_when_quote_fingerprint_already_seen() -> None:
    first = load_sample_email("sample-011")
    second = load_sample_email("sample-012")
    fingerprint = quote_fingerprint(first)
    seen = {fingerprint}

    kind = classify_mail(second, seen_fingerprints=seen, fingerprint=quote_fingerprint(second))

    assert kind == "duplicate"
    assert seen == {fingerprint}


@pytest.mark.unit
def test_classify_mail_returns_quote_when_same_sender_subject_not_in_registry() -> None:
    message = load_sample_email("sample-012")

    assert classify_mail(message, fingerprint=quote_fingerprint(message)) == "quote"


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
