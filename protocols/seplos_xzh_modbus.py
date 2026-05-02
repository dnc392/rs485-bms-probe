from __future__ import annotations
from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

class SeplosXzhModbusCandidateProfile(ProtocolProfile):
    def __init__(self)->None:
        super().__init__("seplos_xzh_modbus_rtu_candidate","SEPLOS V3 / XZH Modbus RTU candidate","rs485",[SerialSettings(9600),SerialSettings(19200)],[ProbeMessage("read_holding_0x0000_16regs_addr1",bytes.fromhex("01 03 00 00 00 10 44 06"),None,500,"unverified_read")],40)
    def split_frames(self, rx_buffer: bytes)->list[bytes]: return [rx_buffer] if len(rx_buffer)>=5 else []
    def validate_response(self, request: ProbeMessage, frame: bytes)->ValidationResult:
        ok = len(frame)>=5
        return ValidationResult(ok, 15 if ok else -50,["seplos xzh candidate frame" if ok else "seplos xzh timeout"])
