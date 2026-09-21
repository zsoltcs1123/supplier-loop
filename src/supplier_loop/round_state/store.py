from __future__ import annotations

import os
import tempfile
from pathlib import Path

from supplier_loop.round_state.models import DedupRegistry, RfqContext, RoundState, SupplierFacts
from supplier_loop.simulator.port import Simulator


def snapshot_world(simulator: Simulator, store: RoundStore) -> RoundState:
    clock = simulator.get_sim_clock()
    assignment = simulator.get_assignment()
    directory = simulator.get_supplier_directory()
    price_history = simulator.get_price_history()
    inbox = simulator.list_inbox()
    suppliers = {
        entry.supplier_id: SupplierFacts(
            supplier_id=entry.supplier_id,
            email=entry.email,
        )
        for entry in directory
    }
    state = RoundState(
        rfq=RfqContext(
            assignment=assignment,
            directory=directory,
            price_history=price_history,
            clock=clock,
        ),
        suppliers=suppliers,
        inbox=inbox,
        dedup=DedupRegistry(),
    )
    store.save(state)
    return state


class RoundStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    def save(self, state: RoundState) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        target = self._root / "round.json"
        fd, tmp_path = tempfile.mkstemp(dir=self._root, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(state.model_dump_json())
            os.replace(tmp_path, target)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def load(self) -> RoundState:
        path = self._root / "round.json"
        return RoundState.model_validate_json(path.read_text(encoding="utf-8"))

    def wipe(self) -> None:
        path = self._root / "round.json"
        if path.exists():
            path.unlink()
