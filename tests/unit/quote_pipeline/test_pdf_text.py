from typing import Any

import pymupdf
import pytest

from supplier_loop.extract.schema import ExtractAttachment
from supplier_loop.quote_pipeline.pdf_text import read_pdf_text, render_pdf_pages
from supplier_loop.quote_pipeline.pipeline import _choose_extract_input


def pdf_with_text(text: str) -> bytes:
    document: Any = pymupdf.open()  # type: ignore[no-untyped-call]
    page = document.new_page()
    page.insert_text((72, 72), text)
    payload = bytes(document.tobytes())
    document.close()
    return payload


def pdf_without_text() -> bytes:
    document: Any = pymupdf.open()  # type: ignore[no-untyped-call]
    document.new_page()
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


@pytest.mark.unit
def test_render_pdf_pages_returns_png_for_blank_page() -> None:
    content = pdf_without_text()

    assert read_pdf_text(content) == ""
    pages = render_pdf_pages(content)

    assert len(pages) == 1
    assert pages[0].startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.unit
def test_choose_extract_input_routes_textless_pdf_to_vision() -> None:
    content = pdf_without_text()
    hints = [ExtractAttachment(filename="quote.pdf", mime_type="application/pdf", content=content)]

    body, vision = _choose_extract_input("email body", hints)

    assert body == "email body"
    assert len(vision) == 1
    assert vision[0].mime_type == "image/png"
    assert vision[0].content.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.unit
def test_choose_extract_input_keeps_text_pdf_off_vision_path() -> None:
    content = pdf_with_text("qty 10 Steel I-Beam 200mm 40.00 USD")
    hints = [ExtractAttachment(filename="quote.pdf", mime_type="application/pdf", content=content)]

    body, vision = _choose_extract_input("email body", hints)

    assert "Steel I-Beam 200mm" in body
    assert vision == []
