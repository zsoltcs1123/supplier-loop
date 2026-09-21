import pytest

from supplier_loop.machine.negotiate import parse_reply_total


@pytest.mark.unit
def test_parse_reply_total_keeps_four_digits_when_no_thousands_comma() -> None:
    assert parse_reply_total("We can meet you at 4116.00 total — confirmed.") == 4116.0


@pytest.mark.unit
def test_parse_reply_total_reads_comma_thousands() -> None:
    assert parse_reply_total("4,200.00") == 4200.0
