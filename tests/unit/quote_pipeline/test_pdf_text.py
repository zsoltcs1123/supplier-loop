from typing import Any

import pymupdf
import pytest

from supplier_loop.quote_pipeline.pdf_text import read_pdf_text


def pdf_with_text(text: str) -> bytes:
    document: Any = pymupdf.open()  # type: ignore[no-untyped-call]
    page = document.new_page()
    page.insert_text((72, 72), text)
    payload = bytes(document.tobytes())
    document.close()
    return payload


@pytest.mark.unit
def test_read_pdf_text_returns_layer_when_pdf_has_text() -> None:
    content = pdf_with_text("qty 10 Steel I-Beam 200mm 40.00 USD")

    text = read_pdf_text(content)

    assert "Steel I-Beam 200mm" in text
    assert "40.00" in text


@pytest.mark.unit
def test_read_pdf_text_returns_empty_when_bytes_are_not_pdf() -> None:
    assert read_pdf_text(b"%PDF-1.4 terms") == ""
    assert read_pdf_text(b"") == ""
