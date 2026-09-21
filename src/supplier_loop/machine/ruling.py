import re

from supplier_loop.machine.correct import correct_once
from supplier_loop.machine.negotiate import negotiate_once
from supplier_loop.round_state.models import RoundState, SupplierFacts
from supplier_loop.simulator.port import EmailMessage, Simulator

_REF_PATTERN = re.compile(r"\[REF:([^\]]+)\]", re.IGNORECASE)
_REJECTION_PATTERN = re.compile(r"\breject|\bdisapprov", re.IGNORECASE)
_APPROVAL_PATTERN = re.compile(r"\bapprov", re.IGNORECASE)
_NEGATION_PATTERN = re.compile(r"\b(?:not|no|never|cannot|cant)\b|n't\b", re.IGNORECASE)


def is_rejection_ruling(body: str) -> bool:
    if _REJECTION_PATTERN.search(body) is not None:
        return True
    return _has_negated_approval(body)


def is_approval_ruling(body: str) -> bool:
    return _APPROVAL_PATTERN.search(body) is not None and not is_rejection_ruling(body)


def _has_negated_approval(body: str) -> bool:
    for match in _APPROVAL_PATTERN.finditer(body):
        window = body[max(0, match.start() - 32) : match.start()]
        if _NEGATION_PATTERN.search(window) is not None:
            return True
    return False


def handle_approver_ruling(
    message: EmailMessage,
    state: RoundState,
    simulator: Simulator,
) -> None:
    supplier_id = _supplier_id_from_subject(message.subject)
    if supplier_id is None or supplier_id not in state.suppliers:
        return
    supplier = state.suppliers[supplier_id]
    supplier.approver_rulings.append(message.body)
    if is_approval_ruling(message.body):
        supplier.phase = "done"
        return
    if not is_rejection_ruling(message.body):
        return
    class_num = _class_from_ruling(message.body, supplier.escalation_classes)
    if class_num in {1, 2, 3, 4}:
        if _revision_already_on_file(supplier):
            supplier.phase = "done"
            return
        supplier.last_rejection_class = class_num
        correct_once(supplier, state, simulator, class_num)
        return
    if class_num == 5:
        negotiate_once(supplier, state, simulator)
        return
    supplier.phase = "done"


def _revision_already_on_file(supplier: SupplierFacts) -> bool:
    return (
        supplier.correction_used
        and supplier.quote is not None
        and supplier.quote.revised_as_sent is not None
    )


def _supplier_id_from_subject(subject: str) -> str | None:
    match = _REF_PATTERN.search(subject)
    if match is None:
        return None
    return match.group(1)


def _class_from_ruling(body: str, escalation_classes: list[int]) -> int:
    for class_num in (1, 2, 3, 4, 5, 6, 7):
        if re.search(rf"\bclass\s+{class_num}\b", body, re.IGNORECASE):
            return class_num
    return _strongest_class(escalation_classes)


def _strongest_class(classes: list[int]) -> int:
    content = sorted(class_num for class_num in classes if class_num in {1, 2, 3, 4, 7})
    if content:
        return content[0]
    if 6 in classes:
        return 6
    if 5 in classes:
        return 5
    if classes:
        return classes[0]
    return 1
