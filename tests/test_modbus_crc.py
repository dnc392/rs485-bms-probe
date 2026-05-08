import pytest

from protocols.modbus_rtu import (
    append_crc,
    build_modbus_read_request,
    crc16_modbus,
    verify_crc,
)


def test_crc16_modbus_known_read_holding_example():
    payload = bytes.fromhex("01 03 00 00 00 0A")

    assert crc16_modbus(payload) == 0xCDC5
    assert append_crc(payload) == bytes.fromhex("01 03 00 00 00 0A C5 CD")
    assert verify_crc(bytes.fromhex("01 03 00 00 00 0A C5 CD"))


def test_crc16_modbus_known_read_holding_0x006b_example():
    payload = bytes.fromhex("01 03 00 6B 00 03")

    assert crc16_modbus(payload) == 0x1774
    assert append_crc(payload) == bytes.fromhex("01 03 00 6B 00 03 74 17")
    assert verify_crc(bytes.fromhex("01 03 00 6B 00 03 74 17"))


def test_build_modbus_read_request_rejects_write_function_codes():
    for function_code in (0x05, 0x06, 0x0F, 0x10):
        with pytest.raises(ValueError, match="only FC03/FC04"):
            build_modbus_read_request(1, function_code, 0x1200, 1)


def test_build_modbus_read_request_validates_crc():
    request = build_modbus_read_request(1, 0x03, 0x1200, 1)

    assert request == bytes.fromhex("01 03 12 00 00 01 81 72")
    assert verify_crc(request)


@pytest.mark.parametrize(
    ("slave_id", "quantity"),
    [
        (0, 1),
        (248, 1),
        (1, 0),
        (1, 65),
    ],
)
def test_build_modbus_read_request_rejects_unsafe_ranges(slave_id, quantity):
    with pytest.raises(ValueError):
        build_modbus_read_request(slave_id, 0x03, 0x1200, quantity)
