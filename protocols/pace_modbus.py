from __future__ import annotations
from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

class PaceModbusProfile(ProtocolProfile):
    def __init__(self)->None:
        super().__init__("pace_rs485_modbus_rtu","PACE RS485 Modbus RTU","rs485",[SerialSettings(9600)],[ProbeMessage("read_main_status_addr0",bytes.fromhex("00 03 00 00 00 0C 44 1E"),None,500,"safe_read")],82)
    def split_frames(self, rx_buffer: bytes)->list[bytes]: return [rx_buffer] if len(rx_buffer)>=5 else []
    def validate_response(self, request: ProbeMessage, frame: bytes)->ValidationResult:
        ok = len(frame)>=5 and frame[1] in (0x03,0x04)
        return ValidationResult(ok, 30 if ok else -50,["modbus function ok" if ok else "modbus invalid"])
