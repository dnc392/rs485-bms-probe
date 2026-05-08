from __future__ import annotations

READ_FUNCTION_CODES = {0x03, 0x04}
MIN_SLAVE_ID = 1
MAX_SLAVE_ID = 247
MAX_READ_QUANTITY = 64


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def append_crc(data: bytes) -> bytes:
    crc = crc16_modbus(data)
    return bytes(data) + crc.to_bytes(2, byteorder="little")


def verify_crc(frame: bytes) -> bool:
    if len(frame) < 4:
        return False
    received_crc = int.from_bytes(frame[-2:], byteorder="little")
    return crc16_modbus(frame[:-2]) == received_crc


def build_modbus_read_request(
    slave_id: int,
    function_code: int,
    start_register: int,
    quantity: int,
) -> bytes:
    if not MIN_SLAVE_ID <= slave_id <= MAX_SLAVE_ID:
        raise ValueError("slave_id must be in range 1..247")
    if function_code not in READ_FUNCTION_CODES:
        raise ValueError("only FC03/FC04 read requests are allowed")
    if not 0 <= start_register <= 0xFFFF:
        raise ValueError("start_register must be in range 0x0000..0xFFFF")
    if not 1 <= quantity <= MAX_READ_QUANTITY:
        raise ValueError("quantity must be in range 1..64")

    request = bytes([slave_id, function_code])
    request += start_register.to_bytes(2, byteorder="big")
    request += quantity.to_bytes(2, byteorder="big")
    return append_crc(request)
