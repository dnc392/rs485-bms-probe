from __future__ import annotations

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

PROFILE_ID = "daly_uart_485"
FRAME_START = 0xA5
REQUEST_ADDRESS = 0x40
RESPONSE_ADDRESSES = (0x01, 0x40)
DATA_LENGTH = 0x08
READ_COMMANDS = tuple(range(0x90, 0x99))
BLOCKED_ACTIONS = (
    "write",
    "mos_control",
    "charging_mos_control",
    "discharging_mos_control",
    "calibration",
    "parameter_set",
    "factory",
    "firmware_update",
    "reset",
)


def daly_checksum(data: bytes) -> int:
    return sum(data) & 0xFF


def build_daly_read_request(command: int) -> bytes:
    if command not in READ_COMMANDS:
        raise ValueError("command must be in read-only range 0x90..0x98")
    frame = bytes([FRAME_START, REQUEST_ADDRESS, command, DATA_LENGTH]) + (b"\x00" * DATA_LENGTH)
    return frame + bytes([daly_checksum(frame)])


def verify_daly_checksum(frame: bytes) -> bool:
    if len(frame) < 13:
        return False
    return frame[12] == daly_checksum(frame[:12])


def _probe(command: int) -> ProbeMessage:
    return ProbeMessage(
        name=f"read_0x{command:02X}",
        tx=build_daly_read_request(command),
        expected_response=bytes([FRAME_START]),
        timeout_ms=500,
        risk="safe_read",
    )


class DalyUart485Profile(ProtocolProfile):
    research_status = "active_safe_read_user_supplied"
    confidence = "frame_level_only"
    read_commands = READ_COMMANDS
    blocked_actions = BLOCKED_ACTIONS

    def __init__(self, response_addresses: tuple[int, ...] = RESPONSE_ADDRESSES) -> None:
        self.response_addresses = response_addresses
        super().__init__(
            PROFILE_ID,
            "DALY UART/RS485 native safe-read",
            "uart_or_rs485",
            [SerialSettings(9600)],
            [_probe(command) for command in READ_COMMANDS],
            80,
            primary_probe_names=("read_0x90",),
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        frames: list[bytes] = []
        index = 0
        while index < len(rx_buffer):
            start = rx_buffer.find(bytes([FRAME_START]), index)
            if start < 0:
                break
            end = start + 13
            if end > len(rx_buffer):
                break
            candidate = rx_buffer[start:end]
            if candidate[3] == DATA_LENGTH:
                frames.append(candidate)
                index = end
            else:
                index = start + 1
        return frames

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        score = 0
        reasons: list[str] = []

        length_ok = len(frame) >= 13
        if length_ok:
            score += 5
            reasons.append("length_ok")
        else:
            score -= 50
            reasons.append("length_invalid")

        frame_start_ok = length_ok and frame[0] == FRAME_START
        if frame_start_ok:
            score += 10
            reasons.append("frame_start_ok")
        else:
            score -= 50
            reasons.append("frame_start_invalid")

        response_address_ok = length_ok and frame[1] in self.response_addresses
        if response_address_ok:
            score += 10
            reasons.append("response_address_ok")
        else:
            score -= 50
            reasons.append("response_address_invalid")

        expected_command = request.tx[2] if len(request.tx) >= 3 else None
        command_ok = length_ok and frame[2] == expected_command
        if command_ok:
            score += 20
            reasons.append("command_ok")
        else:
            score -= 50
            reasons.append("command_mismatch")

        data_length_ok = length_ok and frame[3] == DATA_LENGTH
        if data_length_ok:
            score += 10
            reasons.append("data_length_ok")
        else:
            score -= 50
            reasons.append("data_length_invalid")

        checksum_ok = verify_daly_checksum(frame)
        if checksum_ok:
            score += 20
            reasons.append("checksum_ok")
        else:
            score -= 100
            reasons.append("checksum_invalid")

        not_echo = frame[:13] != request.tx
        if not_echo:
            score += 5
            reasons.append("not_echo")
        else:
            score -= 100
            reasons.append("echoed_request")

        ok = all(
            [
                length_ok,
                frame_start_ok,
                response_address_ok,
                command_ok,
                data_length_ok,
                checksum_ok,
                not_echo,
            ]
        )
        return ValidationResult(ok, score, reasons, self.decode_response(frame))

    def decode_response(self, frame: bytes) -> dict:
        decoded = {
            "raw_hex": frame.hex(" ").upper(),
            "parse_status": "raw_only",
            "checksum_status": "verified" if verify_daly_checksum(frame) else "invalid",
        }
        if len(frame) >= 13:
            decoded.update(
                {
                    "response_address": f"0x{frame[1]:02X}",
                    "command": f"0x{frame[2]:02X}",
                    "data_length": frame[3],
                    "data_hex": frame[4:12].hex(" ").upper(),
                }
            )
        return decoded
