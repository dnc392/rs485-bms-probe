from __future__ import annotations
from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

class JkNativeV2PlaceholderProfile(ProtocolProfile):
    def __init__(self)->None:
        super().__init__("jk_native_rs485_v2_placeholder","JK native RS485 V2.0 placeholder","rs485",[SerialSettings(115200)],[ProbeMessage("passive_first",b"",None,500,"unverified_read")],50)
    def split_frames(self, rx_buffer: bytes)->list[bytes]: return [rx_buffer] if rx_buffer else []
    def validate_response(self, request: ProbeMessage, frame: bytes)->ValidationResult:
        return ValidationResult(bool(frame),10 if frame else -50,["jk placeholder observed frame" if frame else "jk placeholder no frame"])
