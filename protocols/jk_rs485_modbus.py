from __future__ import annotations

from dataclasses import dataclass

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile
from protocols.modbus_rtu import build_modbus_read_request, verify_crc

PROFILE_ID = "jk_rs485_modbus"
DEFAULT_SLAVE_ID = 1
ALLOWED_FUNCTION_CODES = (0x03, 0x04)
FORBIDDEN_FUNCTION_CODES = (0x05, 0x06, 0x0F, 0x10)
CONFIRMED_MODE = "013 (9600) JK BMS RS485 Modbus V1.0"
CONFIRMED_SERIAL = "9600 8N1"
CONFIRMED_PROBE_NAME = "read_cell_voltage_0_addr1"
CONFIRMED_PROBE_ALIAS = "read_cellvol0"
CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME = "read_cell_voltages_0_7_addr1"
CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME = "read_cell_voltages_0_15_addr1"
CONFIRMED_TX_HEX = "01 03 12 00 00 01 81 72"
CONFIRMED_RX_HEX = "01 03 02 0C D8 BD 1E"
CONFIRMED_CELL_BLOCK_0_7_TX_HEX = "01 03 12 00 00 08 41 74"
CONFIRMED_CELL_BLOCK_0_7_RX_HEX = (
    "01 03 10 0C D8 0C D7 0C D7 0C D7 0C D8 0C D7 0C D8 0C D8 72 06"
)
CONFIRMED_CELL_BLOCK_0_15_TX_HEX = "01 03 12 00 00 10 41 7E"
CONFIRMED_CELL_BLOCK_0_15_RX_HEX = (
    "01 03 20 0C D7 0C D7 0C D7 0C D7 0C D7 0C D7 0C D8 0C D7 "
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 26 C8"
)
CONFIRMED_REGISTER = 0x1200
CONFIRMED_QUANTITY = 1
CELL_VOLTAGE_MIN_ACTIVE_MV = 2500
CELL_VOLTAGE_MAX_ACTIVE_MV = 4500


@dataclass(frozen=True)
class JkReadWindow:
    name: str
    function_code: int
    start_register: int
    quantity: int
    risk: str
    source_status: str
    note: str
    primary: bool = False
    hardware_confirmed: bool = False
    aliases: tuple[str, ...] = ()


CONFIRMED_FIRST_READ = JkReadWindow(
    name=CONFIRMED_PROBE_NAME,
    function_code=0x03,
    start_register=CONFIRMED_REGISTER,
    quantity=CONFIRMED_QUANTITY,
    risk="safe_read",
    source_status="hardware_confirmed_single_register",
    note="Hardware-confirmed CellVol0, UINT16, R, mV. Use slave address 1 first.",
    primary=True,
    hardware_confirmed=True,
    aliases=(CONFIRMED_PROBE_ALIAS,),
)

CONFIRMED_CELL_BLOCK_0_7_READ = JkReadWindow(
    name=CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME,
    function_code=0x03,
    start_register=CONFIRMED_REGISTER,
    quantity=8,
    risk="safe_read",
    source_status="hardware_confirmed_primary_cell_voltage_block",
    note="Hardware-confirmed CellVol0..CellVol7, UINT16, R, mV. Primary cell-voltage block.",
    primary=True,
    hardware_confirmed=True,
)

CONFIRMED_CELL_BLOCK_0_15_READ = JkReadWindow(
    name=CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME,
    function_code=0x03,
    start_register=CONFIRMED_REGISTER,
    quantity=16,
    risk="safe_read",
    source_status="hardware_confirmed_extended_cell_voltage_block",
    note="Hardware-confirmed CellVol0..CellVol15, UINT16, R, mV. Extended cell-voltage block.",
    hardware_confirmed=True,
)

CANDIDATE_READ_WINDOWS = (
    CONFIRMED_FIRST_READ,
    CONFIRMED_CELL_BLOCK_0_7_READ,
    CONFIRMED_CELL_BLOCK_0_15_READ,
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
    tx = build_modbus_read_request(
        slave_id=slave_id,
        function_code=window.function_code,
        start_register=window.start_register,
        quantity=window.quantity,
    )
    return ProbeMessage(
        name=window.name,
        tx=tx,
        expected_response=bytes([slave_id, window.function_code]),
        timeout_ms=500,
        risk=window.risk,
        description=window.note,
        slave_id=slave_id,
        function_code=window.function_code,
        start_register=window.start_register,
        quantity=window.quantity,
        primary=window.primary,
        hardware_confirmed=window.hardware_confirmed,
        aliases=window.aliases,
    )


class JkRs485ModbusProfile(ProtocolProfile):
    status = "active_safe_read_hardware_confirmed_cell_voltage_probes"
    research_status = status
    confidence = "hardware_confirmed_cell_voltage_registers"
    hardware_confirmed = True
    confirmed_mode = CONFIRMED_MODE
    confirmed_serial = CONFIRMED_SERIAL
    confirmed_probe = CONFIRMED_PROBE_NAME
    confirmed_probes = (
        CONFIRMED_PROBE_NAME,
        CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME,
        CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME,
    )
    confirmed_tx_hex = CONFIRMED_TX_HEX
    confirmed_rx_hex = CONFIRMED_RX_HEX
    confirmed_probe_captures = {
        CONFIRMED_PROBE_NAME: {"tx_hex": CONFIRMED_TX_HEX, "rx_hex": CONFIRMED_RX_HEX},
        CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME: {
            "tx_hex": CONFIRMED_CELL_BLOCK_0_7_TX_HEX,
            "rx_hex": CONFIRMED_CELL_BLOCK_0_7_RX_HEX,
        },
        CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME: {
            "tx_hex": CONFIRMED_CELL_BLOCK_0_15_TX_HEX,
            "rx_hex": CONFIRMED_CELL_BLOCK_0_15_RX_HEX,
        },
    }
    menu_modes = ("001 JK BMS RS485 Modbus V1.0", "013 (9600) JK BMS RS485 Modbus V1.0")
    allowed_function_codes = ALLOWED_FUNCTION_CODES
    forbidden_function_codes = FORBIDDEN_FUNCTION_CODES
    candidate_read_windows = CANDIDATE_READ_WINDOWS
    probe_aliases = {CONFIRMED_PROBE_ALIAS: CONFIRMED_PROBE_NAME}

    def __init__(self) -> None:
        super().__init__(
            id=PROFILE_ID,
            name="JK BMS RS485 Modbus V1.0 safe-read",
            transport="rs485",
            serial_candidates=[
                SerialSettings(baudrate=9600, parity="N"),
                SerialSettings(baudrate=115200, parity="N"),
            ],
            probes=[
                _probe_from_window(CONFIRMED_FIRST_READ),
                _probe_from_window(CONFIRMED_CELL_BLOCK_0_7_READ),
                _probe_from_window(CONFIRMED_CELL_BLOCK_0_15_READ),
            ],
            confidence_hint=30,
            enabled_by_default=True,
            primary_probe_names=(
                CONFIRMED_FIRST_READ.name,
                CONFIRMED_CELL_BLOCK_0_7_READ.name,
            ),
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        return [rx_buffer] if len(rx_buffer) >= 5 else []

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        score = 0
        reasons: list[str] = []

        if len(frame) < 5:
            return ValidationResult(False, -50, ["short_modbus_frame"], self.decode_response(frame, request, False))

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

        expected_slave = request.slave_id if request.slave_id is not None else request.tx[0]
        expected_function = request.function_code if request.function_code is not None else request.tx[1]
        expected_quantity = request.quantity
        if expected_quantity is None and len(request.tx) >= 6:
            expected_quantity = int.from_bytes(request.tx[4:6], byteorder="big")
        expected_byte_count = expected_quantity * 2 if expected_quantity is not None else None

        if frame[0] == expected_slave:
            reasons.append("slave_id_ok")
            score += 10
        else:
            reasons.append("slave_id_mismatch")
            score -= 50

        is_exception = False
        if frame[1] == expected_function:
            reasons.append("function_code_ok")
            score += 10
        elif frame[1] == (expected_function | 0x80):
            is_exception = True
            reasons.append("modbus_exception_response")
            if len(frame) >= 3:
                reasons.append(f"exception_code_{frame[2]:02X}")
            score -= 50
        else:
            reasons.append("function_code_mismatch")
            score -= 50

        byte_count_ok = False
        if frame[1] == expected_function and len(frame) >= 5 and not is_exception:
            byte_count = frame[2]
            length_ok = len(frame) == byte_count + 5
            expected_count_ok = expected_byte_count is None or byte_count == expected_byte_count
            byte_count_ok = length_ok and expected_count_ok
            if byte_count_ok:
                reasons.append("byte_count_ok")
                score += 10
            else:
                if not expected_count_ok:
                    reasons.append("byte_count_mismatch")
                if not length_ok:
                    reasons.append("response_length_mismatch")
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
        decoded = self.decode_response(frame, request, ok)
        if decoded.get("decode_status") == "hardware_confirmed_single_register":
            reasons.append("decoded_cell_voltage_0_ok")
            score += 10
        elif decoded.get("decode_status") == "hardware_confirmed_cell_voltage_block":
            reasons.append("decoded_cell_voltage_block_ok")
            score += 10
        return ValidationResult(ok=ok, score_delta=score, reasons=reasons, decoded=decoded)

    def decode_response(
        self,
        frame: bytes,
        request: ProbeMessage | None = None,
        validation_ok: bool = False,
    ) -> dict:
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
        if request is not None and not validation_ok:
            decoded["parse_status"] = "validation_error"
            return decoded
        if request is None:
            return decoded
        if not self._is_confirmed_cell_voltage_probe(request):
            decoded["parse_status"] = "raw_only"
            return decoded
        if request.quantity is None or len(frame) != (request.quantity * 2) + 5:
            decoded["parse_status"] = "validation_error"
            return decoded

        values = [
            int.from_bytes(frame[index : index + 2], byteorder="big")
            for index in range(3, 3 + frame[2], 2)
        ]
        decoded.update(_decode_cell_voltage_registers(values, request.start_register or CONFIRMED_REGISTER))
        if self._is_confirmed_cell_voltage_0_probe(request):
            raw_value = values[0]
            decoded.update(
                {
                    "parse_status": "decoded",
                    "decode_status": "hardware_confirmed_single_register",
                    "register_0x1200_raw": raw_value,
                    "cell_voltage_0_mv": raw_value,
                    "cell_voltage_0_v": round(raw_value / 1000, 3),
                }
            )
            return decoded

        decoded.update(
            {
                "parse_status": "decoded",
                "decode_status": "hardware_confirmed_cell_voltage_block",
            }
        )
        return decoded

    @staticmethod
    def _is_confirmed_cell_voltage_probe(request: ProbeMessage) -> bool:
        return (
            JkRs485ModbusProfile._is_confirmed_cell_voltage_0_probe(request)
            or request.name
            in {
                CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME,
                CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME,
            }
        )

    @staticmethod
    def _is_confirmed_cell_voltage_0_probe(request: ProbeMessage) -> bool:
        return (
            request.name == CONFIRMED_PROBE_NAME
            or request.name == CONFIRMED_PROBE_ALIAS
            or CONFIRMED_PROBE_ALIAS in request.aliases
        )


def _decode_cell_voltage_registers(values: list[int], start_register: int) -> dict:
    active_cells: list[dict[str, int]] = []
    out_of_range_registers: list[dict[str, int]] = []
    zero_indices = [index for index, value in enumerate(values) if value == 0]
    nonzero_indices = [index for index, value in enumerate(values) if value != 0]
    last_nonzero_index = max(nonzero_indices) if nonzero_indices else -1
    decode_warnings: list[str] = []

    if any(index < last_nonzero_index for index in zero_indices):
        decode_warnings.append("non_trailing_zero_cell_voltage")

    trailing_zero_indices = [index for index in zero_indices if index > last_nonzero_index]
    if not nonzero_indices:
        trailing_zero_indices = zero_indices

    for index, value in enumerate(values):
        register = start_register + index
        if CELL_VOLTAGE_MIN_ACTIVE_MV <= value <= CELL_VOLTAGE_MAX_ACTIVE_MV:
            active_cells.append({"index": index, "register": register, "mv": value})
        elif value != 0:
            out_of_range_registers.append({"index": index, "register": register, "raw": value})

    active_mv = [cell["mv"] for cell in active_cells]
    decoded = {
        "cell_voltage_registers_mv": values,
        "active_cell_voltages_mv": active_mv,
        "active_cell_voltages_v": [round(value / 1000, 3) for value in active_mv],
        "active_cell_count": len(active_mv),
        "unused_register_indices": trailing_zero_indices,
        "decode_warnings": decode_warnings,
    }
    if active_mv:
        decoded.update(
            {
                "cell_voltage_min_mv": min(active_mv),
                "cell_voltage_max_mv": max(active_mv),
                "cell_voltage_delta_mv": max(active_mv) - min(active_mv),
            }
        )
    if out_of_range_registers:
        decoded["out_of_range_cell_voltage_registers"] = out_of_range_registers
        decoded["decode_warnings"].append("out_of_range_cell_voltage")
    return decoded
