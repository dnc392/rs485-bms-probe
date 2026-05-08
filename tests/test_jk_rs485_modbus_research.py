from pathlib import Path

from protocols.jk_rs485_modbus import CANDIDATE_READ_WINDOWS, CONFIRMED_FIRST_READ
from protocols.modbus_rtu import build_modbus_read_request, verify_crc

PROJECT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DOC = PROJECT_DIR / "docs" / "protocol_research" / "jk_rs485_modbus.md"


def test_jk_rs485_modbus_research_doc_exists_and_contains_safety_terms():
    text = RESEARCH_DOC.read_text(encoding="utf-8")

    assert "001 JK BMS RS485 Modbus V1.0" in text
    assert "013 (9600) JK BMS RS485 Modbus V1.0" in text
    assert "FC03/FC04 only" in text
    assert "FC05/FC06/FC0F/FC10" in text
    assert "address 0" in text
    assert "0x1200" in text
    assert "01 03 12 00 00 01 81 72" in text


def test_confirmed_first_read_request_is_crc_valid():
    request = build_modbus_read_request(
        slave_id=1,
        function_code=CONFIRMED_FIRST_READ.function_code,
        start_register=CONFIRMED_FIRST_READ.start_register,
        quantity=CONFIRMED_FIRST_READ.quantity,
    )

    assert request == bytes.fromhex("01 03 12 00 00 01 81 72")
    assert verify_crc(request)


def test_candidate_windows_do_not_use_write_function_codes():
    assert CANDIDATE_READ_WINDOWS
    for window in CANDIDATE_READ_WINDOWS:
        assert window.function_code in (0x03, 0x04)
        assert window.risk in {"safe_read", "unverified_read"}
        assert 1 <= window.quantity <= 64
