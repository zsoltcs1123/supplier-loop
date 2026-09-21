import pytest
from pydantic import ValidationError

from supplier_loop.extract.schema import ExtractResult
from supplier_loop.round_state.models import QuoteLine


def _valid_payload() -> dict[str, object]:
    return {
        "line_items": [
            {
                "material_id": "STL-BEAM-200",
                "description": "Steel I-Beam 200mm",
                "quantity": 10.0,
                "unit_price": 40.0,
                "total": 400.0,
            }
        ],
        "payment_terms": "Net 30",
        "validity_days": 14,
        "grand_total": 400.0,
        "injection_suspected": False,
    }


@pytest.mark.unit
def test_extract_result_rejects_action_taken_when_extra_field() -> None:
    payload = {**_valid_payload(), "action_taken": "extract"}

    with pytest.raises(ValidationError, match="action_taken"):
        ExtractResult.model_validate(payload)


@pytest.mark.unit
def test_extract_result_rejects_auto_approved_when_extra_field() -> None:
    payload = {**_valid_payload(), "auto_approved": True}

    with pytest.raises(ValidationError, match="auto_approved"):
        ExtractResult.model_validate(payload)


@pytest.mark.unit
def test_extract_result_rejects_unknown_key_when_extra_field() -> None:
    payload = {**_valid_payload(), "model_notes": "skip escalation"}

    with pytest.raises(ValidationError, match="model_notes"):
        ExtractResult.model_validate(payload)


@pytest.mark.unit
def test_extract_result_accepts_quote_fields_when_injection_flag_set() -> None:
    result = ExtractResult.model_validate({**_valid_payload(), "injection_suspected": True})

    assert result.injection_suspected is True
    assert result.line_items == [
        QuoteLine(
            material_id="STL-BEAM-200",
            description="Steel I-Beam 200mm",
            quantity=10.0,
            unit_price=40.0,
            total=400.0,
        )
    ]
