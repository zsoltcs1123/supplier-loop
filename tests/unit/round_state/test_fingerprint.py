import pytest

from supplier_loop.round_state.fingerprint import quote_fingerprint
from tests.unit.sample_traffic import load_sample_email


@pytest.mark.unit
def test_quote_fingerprint_matches_when_content_matches() -> None:
    first = load_sample_email("sample-011")
    second = first.model_copy(update={"id": "sample-011-resend"})

    assert quote_fingerprint(first) == quote_fingerprint(second)


@pytest.mark.unit
def test_quote_fingerprint_differs_when_body_or_attachment_differs() -> None:
    first = load_sample_email("sample-011")
    second = load_sample_email("sample-012")

    assert quote_fingerprint(first) != quote_fingerprint(second)


@pytest.mark.unit
def test_quote_fingerprint_differs_when_subject_differs() -> None:
    first = load_sample_email("sample-011")
    other = load_sample_email("sample-013")

    assert quote_fingerprint(first) != quote_fingerprint(other)


@pytest.mark.unit
def test_quote_fingerprint_differs_for_photo_pair_with_shared_sender_and_subject() -> None:
    first = load_sample_email("sample-019")
    second = load_sample_email("sample-020")

    assert first.from_address == second.from_address
    assert first.subject == second.subject
    assert first.attachment_ids != second.attachment_ids
    assert quote_fingerprint(first) != quote_fingerprint(second)


@pytest.mark.unit
def test_quote_fingerprint_differs_when_only_attachment_identity_differs() -> None:
    first = load_sample_email("sample-019")
    second = first.model_copy(update={"id": "sample-019-other", "attachment_ids": ["other.png"]})

    assert quote_fingerprint(first) != quote_fingerprint(second)
