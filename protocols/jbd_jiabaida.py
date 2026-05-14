from __future__ import annotations

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

PROFILE_ID = "jbd_xiaoxiang_uart_rs485"
FRAME_START = 0xDD
FRAME_END = 0x77
REQUEST_MARKER = 0xA5
READ_COMMANDS = (0x03, 0x04)
BLOCKED_ACTIONS = ("write", "calibration", "factory", "mos_control", "capacity_reset")
OK_STATUS = 0x00
MIN_PAYLOAD_LENGTH_BY_COMMAND = {
    0x03: 1,
    0x04: 2,
}


def jbd_checksum(payload: bytes) -> int:
    return (-sum(payload)) & 0xFFFF


def verify_jbd_checksum(frame: bytes) -> bool:
    if len(frame) < 7 or frame[0] != FRAME_START or frame[-1] != FRAME_END:
        return False

    if frame[1] == REQUEST_MARKER:
        payload = frame[2:-3]
    else:
        payload = frame[3:-3]

    received = int.from_bytes(frame[-3:-1], byteorder="big")
    return received == jbd_checksum(payload)


def _probe(name: str, tx_hex: str, expected_prefix_hex: str) -> ProbeMessage:
    return ProbeMessage(
        name=name,
        tx=bytes.fromhex(tx_hex),
        expected_response=bytes.fromhex(expected_prefix_hex),
        timeout_ms=500,
        risk="safe_read",
    )


class JbdXiaoxiangProfile(ProtocolProfile):
    research_status = "user_supplied_safe_read_profile"
    confidence = "confirmed_frame_shape_and_checksum_only"
    read_commands = READ_COMMANDS
    blocked_actions = BLOCKED_ACTIONS

    def __init__(self) -> None:
        super().__init__(
            PROFILE_ID,
            "JBD / Xiaoxiang UART-RS485",
            "uart_or_rs485",
            [SerialSettings(9600)],
            [
                _probe("read_basic_info", "DD A5 03 00 FF FD 77", "DD 03"),
                _probe("read_cell_voltages", "DD A5 04 00 FF FC 77", "DD 04"),
            ],
            90,
            primary_probe_names=("read_basic_info",),
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        frames: list[bytes] = []
        index = 0
        while index < len(rx_buffer):
            start = rx_buffer.find(bytes([FRAME_START]), index)
            if start < 0:
                break
            if len(rx_buffer) - start < 7:
                break
            data_length = rx_buffer[start + 3]
            frame_length = 7 + data_length
            end = start + frame_length
            if end <= len(rx_buffer) and rx_buffer[end - 1] == FRAME_END:
                frames.append(rx_buffer[start:end])
                index = end
            else:
                index = start + 1
        return frames

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        score = 0
        reasons: list[str] = []

        structure_ok = len(frame) >= 7 and frame[0] == FRAME_START and frame[-1] == FRAME_END
        if structure_ok:
            score += 10
            reasons.append("frame_bounds_ok")
        else:
            score -= 50
            reasons.append("frame_bounds_invalid")

        expected_prefix_ok = bool(request.expected_response and frame.startswith(request.expected_response))
        if expected_prefix_ok:
            score += 20
            reasons.append("expected_prefix_ok")
        else:
            score -= 50
            reasons.append("expected_prefix_mismatch")

        command = request.tx[2] if len(request.tx) >= 4 and request.tx[1] == REQUEST_MARKER else None
        status_ok = False
        if structure_ok and frame[2] == OK_STATUS:
            status_ok = True
            score += 10
            reasons.append("status_ok")
        elif structure_ok:
            score -= 30
            reasons.append("status_not_ok")
        else:
            reasons.append("status_not_checked")

        length_ok = False
        payload_length_ok = False
        if structure_ok:
            data_length = frame[3]
            length_ok = len(frame) == data_length + 7
            if length_ok:
                score += 10
                reasons.append("length_ok")
            else:
                score -= 50
                reasons.append("length_mismatch")

            min_payload_length = MIN_PAYLOAD_LENGTH_BY_COMMAND.get(command, 1)
            payload_length_ok = data_length >= min_payload_length
            if payload_length_ok:
                score += 10
                reasons.append("payload_length_ok")
            else:
                score -= 30
                reasons.append("payload_too_short")

        checksum_ok = verify_jbd_checksum(frame)
        if checksum_ok:
            score += 20
            reasons.append("checksum_ok")
        else:
            score -= 100
            reasons.append("checksum_invalid")

        not_echo = frame != request.tx
        if not_echo:
            score += 5
            reasons.append("not_echo")
        else:
            score -= 100
            reasons.append("echoed_request")

        ok = all([structure_ok, expected_prefix_ok, status_ok, length_ok, payload_length_ok, checksum_ok, not_echo])
        return ValidationResult(ok, score, reasons, self.decode_response(frame))

    def decode_response(self, frame: bytes) -> dict:
        decoded = {
            "raw_hex": frame.hex(" ").upper(),
            "parse_status": "raw_only",
            "checksum_status": "verified" if verify_jbd_checksum(frame) else "invalid",
        }
        if len(frame) >= 7:
            data_length = frame[3]
            decoded.update(
                {
                    "command": f"0x{frame[1]:02X}",
                    "status": f"0x{frame[2]:02X}",
                    "data_length": data_length,
                    "data_hex": frame[4 : 4 + data_length].hex(" ").upper(),
                }
            )
        return decoded


JbdJiabaidaProfile = JbdXiaoxiangProfile
