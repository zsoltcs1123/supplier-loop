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


@pytest.mark.unit
def test_crude_extracts_colon_price_qty_when_live_bullet_body() -> None:
    body = (
        "See pricing.\n"
        "• Steel I-Beam 200mm: $44.65/m x 150 m -> $6697.50\n"
        "• Aluminum Sheet 3mm (AL-SHEET-3): $60.93/sheet x 100 sheet -> $6093.00\n"
        "• PVC Pipe 50mm (PVC-PIPE-50): $4.99/m x 40 m -> $199.60 (min order 50)\n"
        "Payment terms: Net 30\n"
        "Validity: 30 days\n"
        "TOTAL $15014.70\n"
    )
    result = CrudeExtractor().extract(ExtractRequest(email_id="eml_02_0009", body=body))

    assert len(result.line_items) == 3
    first = result.line_items[0]
    assert first.material_id is None
    assert first.description == "Steel I-Beam 200mm"
    assert first.quantity == 150.0
    assert first.unit_price == 44.65
    assert result.line_items[1].material_id == "AL-SHEET-3"
    assert result.payment_terms == "Net 30"
    assert result.validity_days == 30
    assert result.grand_total == 15014.70


@pytest.mark.unit
def test_crude_extracts_colon_qty_price_when_sample_inline_body() -> None:
    body = (
        "Our offer:\n"
        "Steel I-Beam 200mm (STL-BEAM-200): qty 50 m x 42.29 USD/m = 2114.50 USD\n"
        "Copper Wire 10AWG (CU-WIRE-10): qty 40 m x 3.08 USD/m = 123.20 USD\n"
        "Payment Net 30 / validity 30 days / total 9977.25 USD\n"
    )
    result = CrudeExtractor().extract(ExtractRequest(email_id="sample-001", body=body))

    assert len(result.line_items) == 2
    first = result.line_items[0]
    assert first.material_id == "STL-BEAM-200"
    assert first.description == "Steel I-Beam 200mm"
    assert first.quantity == 50.0
    assert first.unit_price == 42.29
    assert result.payment_terms == "Net 30"
    assert result.validity_days == 30
