import re
from collections.abc import Set
from typing import Literal

from supplier_loop.simulator.port import EmailMessage

MailKind = Literal[
    "quote",
    "question",
    "negotiation_reply",
    "duplicate",
    "approver_ruling",
]

APPROVER_ADDRESS = "approver@sim.local"

_QUOTE_WORD = re.compile(r"\b(?:quote|quotation|offer|pricing)\b", re.IGNORECASE)
_ITEM_QTY = re.compile(r"\bqty\s+\d+", re.IGNORECASE)
_ITEM_TIMES = re.compile(r"\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?")
_ITEM_CURRENCY = re.compile(r"(?:USD|\$)\s*\d|(?:\d+(?:[.,]\d+)?\s*USD)", re.IGNORECASE)
_ITEM_THREE_NUMS = re.compile(r"\d+(?:[.,]\d+)?(?:(?:[|\t;]| {2,})\s*\d+(?:[.,]\d+)?){2,}")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_NUMBER_ONLY = re.compile(
    r"^[\s]*(?:USD|EUR|GBP|\$|€|£)?\s*"
    r"(?:\d{1,3}(?:,\d{3})*|\d+)(?:[.,]\d+)?\s*"
    r"(?:USD|EUR|GBP|\$|€|£)?[\s]*$",
    re.IGNORECASE,
)


def classify_mail(
    message: EmailMessage,
    *,
    seen_fingerprints: Set[str] = frozenset(),
    fingerprint: str | None = None,
) -> MailKind:
    if _is_approver_ruling(message):
        return "approver_ruling"
    if _is_question(message):
        return "question"
    if _is_negotiation_reply(message):
        return "negotiation_reply"
    if not _looks_like_quote(message):
        return "question"
    if fingerprint is not None and fingerprint in seen_fingerprints:
        return "duplicate"
    return "quote"


def _is_approver_ruling(message: EmailMessage) -> bool:
    return message.from_address.casefold() == APPROVER_ADDRESS


def _is_question(message: EmailMessage) -> bool:
    if _looks_like_quote(message):
        return False
    if "question" in message.subject.casefold():
        return True
    return "?" in message.body


def _is_negotiation_reply(message: EmailMessage) -> bool:
    if _looks_like_quote(message):
        return False
    blob = f"{message.subject}\n{message.body}".casefold()
    if "meet in the middle" in blob or "meet you at" in blob:
        return True
    return _NUMBER_ONLY.match(message.body.strip()) is not None


def _looks_like_quote(message: EmailMessage) -> bool:
    return _has_price_table(message.body) or _has_quote_attachment(message)


def _has_quote_attachment(message: EmailMessage) -> bool:
    if not message.attachment_ids:
        return False
    blob = f"{message.subject}\n{message.body}"
    return _QUOTE_WORD.search(blob) is not None


def _has_price_table(body: str) -> bool:
    priced = 0
    for line in _content_lines(body):
        if _is_priced_item_line(line):
            priced += 1
            if priced >= 2:
                return True
    return False


def _content_lines(body: str) -> list[str]:
    lines: list[str] = []
    for raw in body.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith(">"):
            continue
        lines.append(stripped)
    return lines


def _is_priced_item_line(line: str) -> bool:
    return bool(
        _ITEM_QTY.search(line)
        or _ITEM_TIMES.search(line)
        or _ITEM_THREE_NUMS.search(line)
        or (_ITEM_CURRENCY.search(line) and len(_NUMBER.findall(line)) >= 2)
    )
