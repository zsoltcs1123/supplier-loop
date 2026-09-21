from collections.abc import Callable
from pathlib import Path

import pytest

from supplier_loop.simulator.mcp import McpSimulator
from supplier_loop.simulator.port import SubmitEntry, SubmitLineItem


class FakeSession:
    def __init__(self) -> None:
        self.tools = ["get_assignment", "get_sim_clock"]
        self.handlers: dict[str, Callable[[dict[str, object] | None], object]] = {}
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def list_tool_names(self) -> list[str]:
        return list(self.tools)

    def call_tool(self, name: str, arguments: dict[str, object] | None = None) -> object:
        self.calls.append((name, arguments))
        return self.handlers[name](arguments)


def _assignment_payload() -> dict[str, object]:
    return {
        "rfq_id": "RFQ-001",
        "required_payment_terms": "Net 30",
        "required_validity_days": 14,
        "target_price_ceiling_pct": 5.0,
        "line_items": [
            {
                "material_id": "STL-BEAM-200",
                "description": "Steel I-Beam 200mm",
                "unit": "m",
                "quantity": 100.0,
            }
        ],
        "goal_statement": "Cover the BOM",
        "approver_email": "approver@sim.local",
        "escalation_subject_protocol": "[REF:<supplier_id>]",
    }


@pytest.mark.unit
def test_mcp_get_assignment_maps_known_fields_when_payload_matches_spec() -> None:
    session = FakeSession()
    session.handlers["get_assignment"] = lambda _args: _assignment_payload()
    simulator = McpSimulator(session)

    assignment = simulator.get_assignment()

    assert assignment.rfq_id == "RFQ-001"
    assert assignment.line_items[0].material_id == "STL-BEAM-200"


@pytest.mark.unit
def test_mcp_list_inbox_maps_from_alias_when_wire_uses_from() -> None:
    session = FakeSession()
    session.handlers["list_inbox"] = lambda _args: [
        {
            "id": "in-1",
            "from": "p01@sim.local",
            "to": "buyer@sim.local",
            "subject": "Quote",
            "sim_time_seconds": 7200,
            "attachments": [{"id": "att-1"}],
        }
    ]
    simulator = McpSimulator(session)

    inbox = simulator.list_inbox()

    assert inbox[0].from_address == "p01@sim.local"
    assert inbox[0].to_address == "buyer@sim.local"
    assert inbox[0].sim_time_hours == 2.0
    assert inbox[0].attachment_ids == ["att-1"]


@pytest.mark.unit
def test_mcp_list_inbox_unwraps_result_when_server_wraps_list() -> None:
    session = FakeSession()
    session.handlers["list_inbox"] = lambda _args: {"result": []}
    simulator = McpSimulator(session)

    assert simulator.list_inbox() == []


@pytest.mark.unit
def test_mcp_list_inbox_maps_sim_time_seconds_when_envelope_omits_to() -> None:
    session = FakeSession()
    session.handlers["list_inbox"] = lambda _args: {
        "result": [
            {
                "id": "in-1",
                "from": "p01@sim.local",
                "subject": "Quote",
                "sim_time": 7200,
                "has_attachments": False,
            }
        ]
    }
    simulator = McpSimulator(session)

    inbox = simulator.list_inbox()

    assert inbox[0].id == "in-1"
    assert inbox[0].from_address == "p01@sim.local"
    assert inbox[0].to_address == ""
    assert inbox[0].sim_time_hours == 2.0


@pytest.mark.unit
def test_mcp_get_sim_clock_defaults_factor_when_missing() -> None:
    session = FakeSession()
    session.handlers["get_sim_clock"] = lambda _args: {
        "sim_time_seconds": 10.0,
        "sim_time_days": 0.0,
        "round_id": "dev-1",
        "mode": "dev",
    }
    simulator = McpSimulator(session)

    clock = simulator.get_sim_clock()

    assert clock.round_id == "dev-1"
    assert clock.clock_factor == 1.0


@pytest.mark.unit
def test_mcp_get_sim_clock_coerces_int_round_id_when_wire_sends_number() -> None:
    session = FakeSession()
    session.handlers["get_sim_clock"] = lambda _args: {
        "sim_time_seconds": 10.0,
        "sim_time_days": 0.0,
        "round_id": 1,
        "mode": "dev",
    }
    simulator = McpSimulator(session)

    assert simulator.get_sim_clock().round_id == "1"


@pytest.mark.unit
def test_mcp_directory_maps_id_and_materials_when_wrapped_in_result() -> None:
    session = FakeSession()
    session.handlers["get_supplier_directory"] = lambda _args: {
        "result": [
            {
                "id": "p01",
                "name": "Marta Novak",
                "email": "p01@sim.local",
                "materials": ["STL-BEAM-200"],
            }
        ]
    }
    simulator = McpSimulator(session)

    directory = simulator.get_supplier_directory()

    assert directory[0].supplier_id == "p01"
    assert directory[0].material_ids == ["STL-BEAM-200"]


@pytest.mark.unit
def test_mcp_price_history_maps_unit_price_when_wrapped_in_prices() -> None:
    session = FakeSession()
    session.handlers["get_price_history"] = lambda _args: {
        "description": "baseline",
        "currency": "USD",
        "prices": [
            {
                "supplier_id": "p01",
                "material_id": "STL-BEAM-200",
                "description": "Steel I-Beam 200mm",
                "unit": "m",
                "unit_price": 40.5,
            }
        ],
    }
    simulator = McpSimulator(session)

    history = simulator.get_price_history()

    assert history[0].last_accepted_unit_price == 40.5


@pytest.mark.unit
def test_mcp_list_sent_records_outbound_when_send_email_succeeds() -> None:
    session = FakeSession()
    session.handlers["send_email"] = lambda _args: {"id": "sent-9"}
    simulator = McpSimulator(session)

    email_id = simulator.send_email("p01@sim.local", "RFQ", "Please quote")

    assert email_id == "sent-9"
    sent = simulator.list_sent()
    assert len(sent) == 1
    assert sent[0].to == "p01@sim.local"
    assert sent[0].subject == "RFQ"
    assert sent[0].body == "Please quote"


@pytest.mark.unit
def test_mcp_list_sent_reloads_outbound_when_sent_log_exists(tmp_path: Path) -> None:
    session = FakeSession()
    session.handlers["send_email"] = lambda _args: {"id": "sent-9"}
    log_path = tmp_path / "sent.json"
    first = McpSimulator(session, sent_log=log_path)
    first.send_email("approver@sim.local", "[REF:p01] class 1", "Class 1: missing BOM line.")

    second = McpSimulator(FakeSession(), sent_log=log_path)
    sent = second.list_sent()

    assert len(sent) == 1
    assert sent[0].id == "sent-9"
    assert sent[0].to == "approver@sim.local"
    assert "[REF:p01]" in sent[0].subject


@pytest.mark.unit
def test_mcp_submit_results_stores_echo_when_warnings_listed() -> None:
    session = FakeSession()
    session.handlers["submit_results"] = lambda _args: {"warnings": ["missing field"]}
    simulator = McpSimulator(session)
    payload = {
        "p01": SubmitEntry(
            line_items=[
                SubmitLineItem(
                    material_id="STL-BEAM-200",
                    quantity=100.0,
                    unit_price=40.0,
                    total=4000.0,
                )
            ],
            payment_terms="Net 30",
            validity_days=14,
            grand_total=4000.0,
            action_taken="extract",
            auto_approved=True,
        )
    }

    echo = simulator.submit_results(payload)

    assert echo.warnings == ["missing field"]
    assert simulator.last_echo() == echo
    assert session.calls[0][0] == "submit_results"
    assert session.calls[0][1] is not None
    assert "results" in session.calls[0][1]


@pytest.mark.unit
def test_mcp_download_attachment_decodes_base64_when_present() -> None:
    session = FakeSession()
    session.handlers["download_attachment"] = lambda _args: {
        "id": "att-1",
        "filename": "quote.pdf",
        "mime_type": "application/pdf",
        "base64": "aGVsbG8=",
    }
    simulator = McpSimulator(session)

    attachment = simulator.download_attachment("att-1")

    assert attachment.content == b"hello"
    assert attachment.filename == "quote.pdf"
