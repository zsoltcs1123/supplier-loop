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
