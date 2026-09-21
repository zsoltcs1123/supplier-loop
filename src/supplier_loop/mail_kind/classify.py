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
    "unknown",
]

APPROVER_ADDRESS = "approver@sim.local"

_ITEM_QTY = re.compile(r"\bqty\s+\d+", re.IGNORECASE)
_ITEM_TIMES = re.compile(r"\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?")
_ITEM_X_TOTAL = re.compile(
    r"\d+(?:[.,]\d+)?\b.*[x×]\s*\d+(?:[.,]\d+)?\b.*\btotal\s+\d+(?:[.,]\d+)?",
    re.IGNORECASE,
)
_ITEM_CURRENCY = re.compile(r"(?:USD|\$)\s*\d|(?:\d+(?:[.,]\d+)?\s*USD)", re.IGNORECASE)
_ITEM_THREE_NUMS = re.compile(r"\d+(?:[.,]\d+)?(?:(?:[|\t;]| {2,})\s*\d+(?:[.,]\d+)?){2,}")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def classify_mail(
    message: EmailMessage,
    *,
    seen_fingerprints: Set[str] = frozenset(),
    fingerprint: str | None = None,
    quote_open: bool = True,
    negotiation_open: bool = False,
    revision_open: bool = False,
) -> MailKind:
    if _is_approver_ruling(message):
        return "approver_ruling"
    if _is_duplicate(message, seen_fingerprints, fingerprint):
        return "duplicate"
    if revision_open and _looks_like_quote(message):
        return "quote"
    if negotiation_open and not _has_price_table(message.body):
        return "negotiation_reply"
    if quote_open and _looks_like_quote(message):
        return "quote"
    if _is_question(message):
        return "question"
    return "unknown"


def _is_approver_ruling(message: EmailMessage) -> bool:
    return message.from_address.casefold() == APPROVER_ADDRESS


def _is_duplicate(
    message: EmailMessage,
    seen_fingerprints: Set[str],
    fingerprint: str | None,
) -> bool:
    if fingerprint is None or fingerprint not in seen_fingerprints:
        return False
    return _looks_like_quote(message)


def _is_question(message: EmailMessage) -> bool:
    if _looks_like_quote(message):
        return False
    if "question" in message.subject.casefold():
        return True
    return "?" in message.body


def _looks_like_quote(message: EmailMessage) -> bool:
    return _has_price_table(message.body) or bool(message.attachment_ids)


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
        or _ITEM_X_TOTAL.search(line)
        or _ITEM_THREE_NUMS.search(line)
        or (_ITEM_CURRENCY.search(line) and len(_NUMBER.findall(line)) >= 2)
    )
