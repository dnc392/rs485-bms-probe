from __future__ import annotations
from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

class DalyUartNativeProfile(ProtocolProfile):
    def __init__(self)->None:
        super().__init__("daly_uart_485_native","DALY UART/485 native","uart_or_rs485",[SerialSettings(9600)],[ProbeMessage("read_soc_status_candidate",b"\xA5\x40\x90\x08",None,500,"unverified_read")],70)
    def split_frames(self, rx_buffer: bytes)->list[bytes]:
        return [rx_buffer] if rx_buffer else []
    def validate_response(self, request: ProbeMessage, frame: bytes)->ValidationResult:
        ok = len(frame) >= 4
        return ValidationResult(ok, 20 if ok else -50,["daly candidate length ok" if ok else "daly timeout/invalid"])
