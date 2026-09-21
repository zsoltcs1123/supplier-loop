from pathlib import Path

import pytest

from supplier_loop.extract.crude import CrudeExtractor
from supplier_loop.extract.schema import ExtractRequest

_FIXTURE = Path("docs/fixtures/example_artifacts/inline-text_email_body.txt")


@pytest.mark.unit
def test_crude_extracts_qty_lines_when_happy_path_body() -> None:
    body = (
        "Quote for your RFQ\n"
        "qty 100 Steel I-Beam 200mm 40.00 USD\n"
        "qty 50 Aluminum Plate 10mm 25.00 USD\n"
        "Payment Net 30, validity 14 days"
    )
    result = CrudeExtractor().extract(ExtractRequest(email_id="in-1", body=body))

    assert len(result.line_items) == 2
    assert result.line_items[0].description == "Steel I-Beam 200mm"
    assert result.line_items[0].quantity == 100.0
    assert result.line_items[0].unit_price == 40.0
    assert result.payment_terms == "Net 30"
    assert result.validity_days == 14
    assert result.injection_suspected is False


@pytest.mark.unit
def test_crude_extracts_bullet_lines_when_inline_text_fixture() -> None:
    body = _FIXTURE.read_text(encoding="utf-8")
    result = CrudeExtractor().extract(ExtractRequest(email_id="in-1", body=body))

    assert len(result.line_items) == 8
    first = result.line_items[0]
    assert first.material_id == "STL-BEAM-200"
    assert first.description == "Steel I-Beam 200mm"
    assert first.quantity == 20.0
    assert first.unit_price == 41.97
    assert result.payment_terms == "Net 30"
    assert result.validity_days == 30
    assert result.grand_total == 16068.0


@pytest.mark.unit
def test_crude_returns_empty_lines_when_body_has_no_quote() -> None:
    result = CrudeExtractor().extract(ExtractRequest(email_id="in-1", body="see attached PDF"))

    assert result.line_items == []
    assert result.payment_terms == ""
    assert result.validity_days == 0
    assert result.grand_total == 0.0
