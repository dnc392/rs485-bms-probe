from __future__ import annotations
from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

class SeplosAsciiProfile(ProtocolProfile):
    def __init__(self)->None:
        super().__init__("seplos_rs485_ascii","SEPLOS RS485 ASCII","rs485",[SerialSettings(9600)],[ProbeMessage("safe_read_candidate",b"~SEPLOS?\r",None,500,"unverified_read")],60)
    def split_frames(self, rx_buffer: bytes)->list[bytes]:
        return [c+b"\r" for c in rx_buffer.split(b"\r") if b"~" in c]
    def validate_response(self, request: ProbeMessage, frame: bytes)->ValidationResult:
        ok = frame.startswith(b"~") and frame.endswith(b"\r")
        return ValidationResult(ok, 20 if ok else -50,["seplos ascii frame ok" if ok else "seplos frame invalid"])
