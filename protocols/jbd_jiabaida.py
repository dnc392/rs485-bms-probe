from __future__ import annotations
from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

class JbdJiabaidaProfile(ProtocolProfile):
    def __init__(self) -> None:
        super().__init__("jbd_jiabaida_uart_rs485","JBD / Jiabaida UART-RS485","uart_or_rs485",[SerialSettings(9600)],[
            ProbeMessage("read_basic_info", bytes.fromhex("DD A5 03 00 FF FD 77"), None, 500, "safe_read"),
            ProbeMessage("read_cell_voltages", bytes.fromhex("DD A5 04 00 FF FC 77"), None, 500, "safe_read"),
        ],90)
    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        return [rx_buffer] if rx_buffer.startswith(b"\xDD") and rx_buffer.endswith(b"w") else []
    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        ok = frame.startswith(b"\xDD") and frame.endswith(b"w")
        return ValidationResult(ok, 40 if ok else -50, ["jbd frame ok" if ok else "jbd frame invalid"])
