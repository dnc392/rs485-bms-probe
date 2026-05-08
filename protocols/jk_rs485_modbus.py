from __future__ import annotations

from dataclasses import dataclass

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile
from protocols.modbus_rtu import build_modbus_read_request, verify_crc

PROFILE_ID = "jk_rs485_modbus"
DEFAULT_SLAVE_ID = 1
ALLOWED_FUNCTION_CODES = (0x03, 0x04)
FORBIDDEN_FUNCTION_CODES = (0x05, 0x06, 0x0F, 0x10)


@dataclass(frozen=True)
class JkReadWindow:
    name: str
    function_code: int
    start_register: int
    quantity: int
    risk: str
    source_status: str
    note: str


CONFIRMED_FIRST_READ = JkReadWindow(
    name="read_cell_voltage_0_addr1",
    function_code=0x03,
    start_register=0x1200,
    quantity=1,
    risk="safe_read",
    source_status="source_confirmed_register",
    note="CellVol0, UINT16, R, mV. Use slave address 1 first.",
)

CANDIDATE_READ_WINDOWS = (
    CONFIRMED_FIRST_READ,
    JkReadWindow(
        name="read_cell_voltages_0_31_addr1",
        function_code=0x03,
        start_register=0x1200,
        quantity=32,
        risk="unverified_read",
        source_status="source_confirmed_register_window",
        note="CellVol0..CellVol31, UINT16, R, mV. Larger read window needs hardware confirmation.",
    ),
    JkReadWindow(
        name="read_pack_voltage_current_status_addr1",
        function_code=0x03,
        start_register=0x1290,
        quantity=10,
        risk="unverified_read",
        source_status="source_confirmed_register_window",
        note="BatVol, BatWatt, BatCurrent, TempBat1/2, alarm bits. Larger read window needs hardware confirmation.",
    ),
    JkReadWindow(
        name="read_soc_capacity_cycles_addr1",
        function_code=0x03,
        start_register=0x12A4,
        quantity=11,
        risk="unverified_read",
        source_status="source_confirmed_register_window",
        note="Balancing current/state, SOC, capacity, cycle counters, SOH/precharge.",
    ),
    JkReadWindow(
        name="read_manufacturer_model_addr1",
        function_code=0x03,
        start_register=0x1400,
        quantity=8,
        risk="unverified_read",
        source_status="source_confirmed_register_window",
        note="ManufacturerDeviceID ASCII, R. Metadata read only; verify response before decoding.",
    ),
)


def _probe_from_window(window: JkReadWindow, slave_id: int = DEFAULT_SLAVE_ID) -> ProbeMessage:
    return ProbeMessage(
        name=window.name,
        tx=build_modbus_read_request(
            slave_id=slave_id,
            function_code=window.function_code,
            start_register=window.start_register,
            quantity=window.quantity,
        ),
        expected_response=bytes([slave_id, window.function_code]),
        timeout_ms=500,
        risk=window.risk,
        description=window.note,
    )


class JkRs485ModbusProfile(ProtocolProfile):
    research_status = "research_inactive"
    confidence = "research_only"
    menu_modes = ("001 JK BMS RS485 Modbus V1.0", "013 (9600) JK BMS RS485 Modbus V1.0")
    allowed_function_codes = ALLOWED_FUNCTION_CODES
    forbidden_function_codes = FORBIDDEN_FUNCTION_CODES
    candidate_read_windows = CANDIDATE_READ_WINDOWS

    def __init__(self) -> None:
        super().__init__(
            id=PROFILE_ID,
            name="JK BMS RS485 Modbus V1.0 research inactive",
            transport="rs485",
            serial_candidates=[
                SerialSettings(baudrate=9600, parity="N"),
                SerialSettings(baudrate=115200, parity="N"),
            ],
            probes=[_probe_from_window(CONFIRMED_FIRST_READ)],
            confidence_hint=30,
            enabled_by_default=False,
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        return [rx_buffer] if len(rx_buffer) >= 5 else []

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        score = 0
        reasons: list[str] = []

        if len(frame) < 5:
            return ValidationResult(False, -50, ["short_modbus_frame"])

        if frame == request.tx:
            reasons.append("echoed_request")
            score -= 100
        else:
            reasons.append("not_echo")
            score += 5

        if verify_crc(frame):
            reasons.append("crc_ok")
            score += 25
        else:
            reasons.append("crc_invalid")
            score -= 100

        expected_slave = request.tx[0]
        expected_function = request.tx[1]
        if frame[0] == expected_slave:
            reasons.append("slave_id_ok")
            score += 10
        else:
            reasons.append("slave_id_mismatch")
            score -= 50

        if frame[1] == expected_function:
            reasons.append("function_code_ok")
            score += 10
        elif frame[1] == (expected_function | 0x80):
            reasons.append("exception_response")
            score -= 50
        else:
            reasons.append("function_code_mismatch")
            score -= 50

        byte_count_ok = False
        if frame[1] == expected_function and len(frame) >= 5:
            byte_count = frame[2]
            byte_count_ok = len(frame) == byte_count + 5
            if byte_count_ok:
                reasons.append("byte_count_ok")
                score += 10
            else:
                reasons.append("byte_count_mismatch")
                score -= 50

        ok = all(
            [
                frame != request.tx,
                verify_crc(frame),
                frame[0] == expected_slave,
                frame[1] == expected_function,
                byte_count_ok,
            ]
        )
        return ValidationResult(ok=ok, score_delta=score, reasons=reasons, decoded=self.decode_response(frame))

    def decode_response(self, frame: bytes) -> dict:
        decoded = {
            "raw_hex": frame.hex(" ").upper(),
            "parse_status": "raw_only",
            "crc_status": "verified" if verify_crc(frame) else "invalid",
        }
        if len(frame) >= 5:
            decoded.update(
                {
                    "slave_id": frame[0],
                    "function_code": frame[1],
                    "byte_count": frame[2] if frame[1] in ALLOWED_FUNCTION_CODES else None,
                }
            )
        return decoded
