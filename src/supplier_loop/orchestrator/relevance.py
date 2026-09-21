from supplier_loop.round_state.models import RoundState
from supplier_loop.simulator.port import BomLine, SupplierEntry


def bom_material_ids(state: RoundState) -> frozenset[str]:
    return frozenset(line.material_id for line in state.rfq.assignment.line_items)


def relevant_supplier_ids(state: RoundState) -> frozenset[str]:
    materials = bom_material_ids(state)
    return frozenset(
        entry.supplier_id for entry in state.rfq.directory if materials & set(entry.material_ids)
    )


def supplier_catalog(state: RoundState, supplier_id: str) -> frozenset[str]:
    for entry in state.rfq.directory:
        if entry.supplier_id == supplier_id:
            return frozenset(entry.material_ids)
    return frozenset()


def bom_lines_for_supplier(state: RoundState, supplier_id: str) -> list[BomLine]:
    catalog = supplier_catalog(state, supplier_id)
    return [line for line in state.rfq.assignment.line_items if line.material_id in catalog]


def supplier_for_address(state: RoundState, from_address: str) -> SupplierEntry | None:
    lowered = from_address.casefold()
    for entry in state.rfq.directory:
        if entry.email.casefold() == lowered:
            return entry
    return None
