from __future__ import annotations

import base64
import json
from collections.abc import Mapping, Sequence
from typing import TypeVar, cast

from pydantic import BaseModel

from supplier_loop.simulator.port import (
    Assignment,
    Attachment,
    EmailMessage,
    InboxEntry,
    PriceHistoryRow,
    SimClock,
    SubmitEcho,
    SupplierEntry,
)

T = TypeVar("T", bound=BaseModel)


def parse_assignment(payload: object) -> Assignment:
    data = _unwrap_object(payload, "assignment")
    return _validate(Assignment, data)


def parse_directory(payload: object) -> list[SupplierEntry]:
    items = _as_list(payload, "suppliers", "directory")
    return [_parse_supplier(item) for item in items]


def parse_price_history(payload: object) -> list[PriceHistoryRow]:
    items = _as_list(payload, "price_history", "history", "rows", "prices")
    return [_parse_price_row(item) for item in items]


def parse_clock(payload: object) -> SimClock:
    data = dict(_unwrap_object(payload, "clock"))
    if "clock_factor" not in data and "clockFactor" not in data:
        data["clock_factor"] = 1.0
    round_id = _get(data, "round_id")
    if round_id is not None:
        data["round_id"] = _as_text(round_id)
    return _validate(SimClock, data)


def parse_inbox(payload: object) -> list[InboxEntry]:
    items = _as_list(payload, "inbox", "emails", "messages")
    return [parse_inbox_entry(item) for item in items]


def parse_inbox_entry(payload: object) -> InboxEntry:
    data = _as_object(payload)
    return InboxEntry(
        id=_require_str(data, "id"),
        from_address=_require_str(data, "from_address", "from", "fromAddress", "from_email"),
        to_address=_as_text(_get(data, "to_address", "to", "toAddress", "to_email")) or "",
        subject=_require_str(data, "subject"),
        sim_time_hours=_inbox_hours(data),
        attachment_ids=_attachment_ids(data),
    )


def parse_email(payload: object) -> EmailMessage:
    data = _unwrap_object(payload, "email", "message")
    entry = parse_inbox_entry(data)
    body = _optional_str(data, "body") or ""
    return EmailMessage(
        id=entry.id,
        from_address=entry.from_address,
        to_address=entry.to_address,
        subject=entry.subject,
        sim_time_hours=entry.sim_time_hours,
        attachment_ids=entry.attachment_ids,
        body=body,
    )


def parse_attachment(payload: object) -> Attachment:
    data = _unwrap_object(payload, "attachment")
    encoded = _optional_str(data, "base64", "content_base64")
    content = _optional_bytes(data, "content")
    if encoded is not None:
        content = base64.b64decode(encoded)
    if content is None:
        raise ValueError("attachment is missing content")
    return Attachment(
        id=_require_str(data, "id"),
        filename=_require_str(data, "filename", "name"),
        mime_type=_require_str(data, "mime_type", "mimeType"),
        content=content,
    )


def parse_send_id(payload: object) -> str:
    if payload is None:
        raise ValueError("send_email returned no id")
    text = _as_text(payload)
    if text:
        return text
    data = _as_object(payload)
    return _require_str(data, "id", "email_id", "emailId")


def parse_echo(payload: object) -> SubmitEcho:
    if payload is None:
        return SubmitEcho(warnings=[])
    if isinstance(payload, list):
        return SubmitEcho(warnings=[str(item) for item in payload])
    data = _as_object(payload)
    raw = _get(data, "warnings")
    if raw is None:
        return SubmitEcho(warnings=[])
    if isinstance(raw, str):
        return SubmitEcho(warnings=[raw])
    if isinstance(raw, list):
        return SubmitEcho(warnings=[str(item) for item in raw])
    raise TypeError("warnings must be a list or string")


def _parse_supplier(payload: object) -> SupplierEntry:
    data = dict(_as_object(payload))
    if _get(data, "supplier_id") is None and _get(data, "id") is not None:
        data["supplier_id"] = _get(data, "id")
    if _get(data, "material_ids") is None and _get(data, "materials") is not None:
        data["material_ids"] = _get(data, "materials")
    return _validate(SupplierEntry, data)


def _parse_price_row(payload: object) -> PriceHistoryRow:
    data = dict(_as_object(payload))
    if _get(data, "last_accepted_unit_price") is None and _get(data, "unit_price") is not None:
        data["last_accepted_unit_price"] = _get(data, "unit_price")
    return _validate(PriceHistoryRow, data)


def _validate(model: type[T], data: Mapping[str, object]) -> T:
    picked: dict[str, object] = {}
    for name in model.model_fields:
        value = _get(data, name)
        if value is not None:
            picked[name] = value
    return model.model_validate(picked)


def _unwrap_object(payload: object, *keys: str) -> Mapping[str, object]:
    data = _as_object(payload)
    if len(data) == 1:
        key = next(iter(data))
        if key in keys or key in {"result", "data"}:
            inner = data[key]
            if isinstance(inner, Mapping):
                return cast(Mapping[str, object], inner)
    return data


def _as_list(payload: object, *keys: str) -> list[object]:
    payload = _maybe_json(payload)
    if isinstance(payload, list):
        return list(payload)
    data = _as_object(payload)
    for key in (*keys, "result", "data"):
        value = _get(data, key)
        if isinstance(value, list):
            return list(value)
    raise TypeError(f"expected list, got {type(payload).__name__}")


def _as_object(payload: object) -> Mapping[str, object]:
    payload = _maybe_json(payload)
    if isinstance(payload, Mapping):
        return cast(Mapping[str, object], payload)
    raise TypeError(f"expected object, got {type(payload).__name__}")


def _maybe_json(payload: object) -> object:
    if isinstance(payload, str):
        try:
            parsed: object = json.loads(payload)
        except json.JSONDecodeError:
            return payload
        return parsed
    return payload


def _get(data: Mapping[str, object], *names: str) -> object | None:
    for name in names:
        if name in data:
            return data[name]
        camel = _camel(name)
        if camel in data:
            return data[camel]
    return None


def _require_str(data: Mapping[str, object], *names: str) -> str:
    text = _as_text(_get(data, *names))
    if text:
        return text
    raise ValueError(f"missing string field {names[0]}")


def _optional_str(data: Mapping[str, object], *names: str) -> str | None:
    return _as_text(_get(data, *names))


def _as_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return str(value)
    return None


def _optional_bytes(data: Mapping[str, object], *names: str) -> bytes | None:
    value = _get(data, *names)
    if isinstance(value, bytes):
        return value
    return None


def _inbox_hours(data: Mapping[str, object]) -> float:
    hours = _get(data, "sim_time_hours", "simTimeHours")
    if hours is not None:
        return float(cast(int | float | str, hours))
    seconds = _get(data, "sim_time_seconds", "simTimeSeconds", "sim_time", "simTime")
    if seconds is not None:
        return float(cast(int | float | str, seconds)) / 3600.0
    raise ValueError("inbox entry missing sim time")


def _attachment_ids(data: Mapping[str, object]) -> list[str]:
    raw = _get(data, "attachment_ids", "attachmentIds", "attachments")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise TypeError("attachment_ids must be a list")
    ids: list[str] = []
    for item in cast(Sequence[object], raw):
        if isinstance(item, str | int | float) and not isinstance(item, bool):
            ids.append(str(item))
            continue
        if isinstance(item, Mapping):
            mapped = cast(Mapping[str, object], item)
            ids.append(_require_str(mapped, "id"))
            continue
        raise TypeError("attachment id must be a string")
    return ids


def _camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])
