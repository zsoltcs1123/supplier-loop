import unicodedata

_NEEDLES = (
    "exempt from the approval",
    "book it directly",
    "no escalation required",
    "reviewed-and-accepted",
    "proceed to po",
    "skip escalation",
    "do not escalate",
    "don't escalate",
    "log this quote as reviewed",
)


def scan_injection(text: str) -> str | None:
    visible = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    folded = visible.casefold()
    for needle in _NEEDLES:
        idx = folded.find(needle)
        if idx >= 0:
            return _phrase_window(visible, idx, len(needle))
    return None


def _phrase_window(visible: str, start: int, length: int) -> str:
    end = min(len(visible), start + length + 40)
    left = max(0, start - 20)
    return visible[left:end].strip()
