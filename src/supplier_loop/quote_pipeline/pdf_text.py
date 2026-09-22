from __future__ import annotations

from typing import Any

import pymupdf


def read_pdf_text(content: bytes) -> str:
    if not content:
        return ""
    try:
        document: Any = pymupdf.open(stream=content, filetype="pdf")  # type: ignore[no-untyped-call]
    except pymupdf.FileDataError:
        return ""
    try:
        chunks = [str(page.get_text()).strip() for page in document]
    finally:
        document.close()
    return "\n\n".join(chunk for chunk in chunks if chunk)


def render_pdf_pages(content: bytes, *, dpi: int = 150) -> list[bytes]:
    if not content:
        return []
    try:
        document: Any = pymupdf.open(stream=content, filetype="pdf")  # type: ignore[no-untyped-call]
    except pymupdf.FileDataError:
        return []
    pages: list[bytes] = []
    try:
        for page in document:
            pixmap = page.get_pixmap(dpi=dpi)
            pages.append(pixmap.tobytes("png"))
    except pymupdf.FileDataError:
        return []
    finally:
        document.close()
    return pages
