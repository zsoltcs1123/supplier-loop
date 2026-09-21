import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from supplier_loop.extract.openrouter import OPENROUTER_URL, OpenRouterExtractor
from supplier_loop.extract.schema import ExtractAttachment, ExtractRequest
from supplier_loop.extract.spend import SpendCapReached, load_spend, record_spend
from supplier_loop.round_state.models import QuoteLine


def _quoted_payload() -> dict[str, object]:
    return {
        "line_items": [
            {
                "material_id": "STL-BEAM-200",
                "description": "Steel I-Beam 200mm",
                "quantity": 10.0,
                "unit_price": 40.0,
                "total": 400.0,
                "action_taken": "extract",
            }
        ],
        "payment_terms": "Net 30",
        "validity_days": 14,
        "grand_total": 400.0,
        "injection_suspected": False,
        "auto_approved": True,
    }


def _response(payload: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "choices": [{"message": {"content": json.dumps(payload or _quoted_payload())}}],
        "usage": {"cost": 0.0012, "prompt_tokens": 11, "completion_tokens": 22},
    }


class _Poster:
    def __init__(self, response: dict[str, object] | None = None) -> None:
        self.response = response or _response()
        self.calls: list[tuple[str, Mapping[str, str], Mapping[str, object]]] = []

    def __call__(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
    ) -> object:
        self.calls.append((url, headers, payload))
        return self.response


def _extractor(tmp_path: Path, poster: _Poster) -> OpenRouterExtractor:
    return OpenRouterExtractor(
        api_key="sk-test",
        model="openai/gpt-4o-mini",
        spend_path=tmp_path / "llm-spend.json",
        post=poster,
    )


@pytest.mark.unit
def test_openrouter_extracts_quote_fields_and_drops_extra_keys(tmp_path: Path) -> None:
    poster = _Poster()
    result = _extractor(tmp_path, poster).extract(
        ExtractRequest(email_id="in-1", body="qty 10 Steel I-Beam 200mm 40.00 USD")
    )

    assert result.line_items == [
        QuoteLine(
            material_id="STL-BEAM-200",
            description="Steel I-Beam 200mm",
            quantity=10.0,
            unit_price=40.0,
            total=400.0,
        )
    ]
    assert result.payment_terms == "Net 30"
    assert result.injection_suspected is False
    url, headers, payload = poster.calls[0]
    assert url == OPENROUTER_URL
    assert headers["Authorization"] == "Bearer sk-test"
    assert payload["model"] == "openai/gpt-4o-mini"
    messages = payload["messages"]
    assert isinstance(messages, list)
    user = messages[1]
    assert isinstance(user, dict)
    assert user["content"] == "qty 10 Steel I-Beam 200mm 40.00 USD"


@pytest.mark.unit
def test_openrouter_treats_string_null_sku_as_missing(tmp_path: Path) -> None:
    payload = _quoted_payload()
    lines = payload["line_items"]
    assert isinstance(lines, list)
    first = lines[0]
    assert isinstance(first, dict)
    first["material_id"] = "null"
    poster = _Poster(_response(payload))

    result = _extractor(tmp_path, poster).extract(ExtractRequest(email_id="in-1", body="quote"))

    assert result.line_items[0].material_id is None


@pytest.mark.unit
def test_openrouter_sends_image_parts_when_photo_attached(tmp_path: Path) -> None:
    poster = _Poster()
    _extractor(tmp_path, poster).extract(
        ExtractRequest(
            email_id="in-1",
            body="quote attached as photo",
            attachments=[
                ExtractAttachment(
                    filename="quote.png",
                    mime_type="image/png",
                    content=b"\x89PNG\r\n",
                )
            ],
        )
    )

    payload = poster.calls[0][2]
    messages = payload["messages"]
    assert isinstance(messages, list)
    user = messages[1]
    assert isinstance(user, dict)
    content = user["content"]
    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": "quote attached as photo"}
    image = content[1]
    assert isinstance(image, dict)
    assert image["type"] == "image_url"
    url = image["image_url"]
    assert isinstance(url, dict)
    assert str(url["url"]).startswith("data:image/png;base64,")


@pytest.mark.unit
def test_openrouter_records_usage_cost_on_the_spend_ledger(tmp_path: Path) -> None:
    path = tmp_path / "llm-spend.json"
    poster = _Poster()
    OpenRouterExtractor(
        api_key="sk-test",
        spend_path=path,
        post=poster,
    ).extract(ExtractRequest(email_id="in-1", body="quote"))

    ledger = load_spend(path)
    assert ledger.used == 0.0012
    assert ledger.calls[0].prompt_tokens == 11
    assert ledger.calls[0].completion_tokens == 22


@pytest.mark.unit
def test_openrouter_refuses_extract_when_spend_cap_reached(tmp_path: Path) -> None:
    path = tmp_path / "llm-spend.json"
    record_spend(
        model="openai/gpt-4o-mini",
        cost=100.0,
        prompt_tokens=1,
        completion_tokens=1,
        path=path,
    )
    poster = _Poster()

    with pytest.raises(SpendCapReached, match="spend cap"):
        OpenRouterExtractor(
            api_key="sk-test",
            spend_path=path,
            post=poster,
        ).extract(ExtractRequest(email_id="in-1", body="quote"))

    assert poster.calls == []
