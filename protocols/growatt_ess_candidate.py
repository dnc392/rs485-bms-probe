from __future__ import annotations
from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

class GrowattEssCandidateProfile(ProtocolProfile):
    def __init__(self)->None:
        super().__init__("growatt_ess_rs485_candidate","Growatt ESS RS485 candidate profile","rs485",[SerialSettings(9600),SerialSettings(19200)],[ProbeMessage("generic_modbus_read_addr1_holding_0x0000_16",bytes.fromhex("01 03 00 00 00 10 44 06"),None,500,"unverified_read")],35)
    def split_frames(self, rx_buffer: bytes)->list[bytes]: return [rx_buffer] if len(rx_buffer)>=5 else []
    def validate_response(self, request: ProbeMessage, frame: bytes)->ValidationResult:
        ok = len(frame)>=5
        return ValidationResult(ok, 10 if ok else -50,["growatt candidate frame" if ok else "growatt timeout"])
