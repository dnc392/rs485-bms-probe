from __future__ import annotations

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile
from protocols.modbus_rtu import build_modbus_read_request, verify_crc

PROFILE_ID = "pace_rs485_modbus_v1_3"
ALLOWED_FUNCTION_CODES = (0x03, 0x04)
FORBIDDEN_FUNCTION_CODES = (0x05, 0x06, 0x0F, 0x10)
CONFIRMED_SOURCE = "PACE BMS Modbus Protocol for RS485 V1.3 (2017-06-27)"
SOURCE_PROBE_NAME = "read_pack_voltage_addr1"
SOURCE_TX_HEX = "01 03 00 01 00 01 D5 CA"
CONFIRMED_RX_HEX = "01 03 02 0A 45 7F 17"
BULK_CORE_PROBE_NAME = "read_core_block_0_48_addr1"
BULK_CORE_TX_HEX = "01 03 00 00 00 31 84 1E"
BULK_CORE_CONFIRMED_RX_HEX = ""
BULK_CORE_EXCEPTION_RX_HEX = "01 83 02 C0 F1"
BASIC_BLOCK_PROBE_NAME = "read_basic_block_0_2_addr1"
BASIC_BLOCK_TX_HEX = "01 03 00 00 00 03 05 CB"
BASIC_BLOCK_CONFIRMED_RX_HEX = "01 03 06 00 00 0A 45 00 42 B3 49"
CELL8_PROBE_NAME = "read_cell_voltages_0_7_addr1"
CELL8_TX_HEX = "01 03 00 15 00 08 55 C8"
CELL8_CONFIRMED_RX_HEX = "01 03 10 0C D8 0C D7 00 00 00 00 00 00 00 00 00 00 00 00 01 DC"
CELL16_PROBE_NAME = "read_cell_voltages_0_15_addr1"
CELL16_TX_HEX = "01 03 00 15 00 10 55 C2"
CELL16_CONFIRMED_RX_HEX = "01 03 20 0C D7 0C D5 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 D2 00 D1 F8 30 F8 30 00 F1 00 D1 64 1A"
CONFIRMED_SERIAL = "9600 8N1"
CONFIRMED_BMS_MENU = "004 PACE_RS485_Modbus_V1.3"
MIN_PLAUSIBLE_CELL_MV = 2500
MAX_PLAUSIBLE_CELL_MV = 4500
CELL8_SEMANTIC_WARNING = (
    "Only first 2 values look like valid cell voltages; trailing zeros may be unused or mapping mismatch."
)


def _with_probe_metadata(probe: ProbeMessage, **metadata) -> ProbeMessage:
    for key, value in metadata.items():
        setattr(probe, key, value)
    return probe


def _pack_voltage_probe() -> ProbeMessage:
    return _with_probe_metadata(
        ProbeMessage(
            name=SOURCE_PROBE_NAME,
            tx=build_modbus_read_request(1, 0x03, 0x0001, 1),
            expected_response=bytes([1, 0x03]),
            timeout_ms=500,
            risk="safe_read",
            description="Source-confirmed PACE pack voltage, register 0001, UINT16, unit 10mV.",
            slave_id=1,
            function_code=0x03,
            start_register=0x0001,
            quantity=1,
            primary=True,
            hardware_confirmed=True,
        ),
        modbus_frame_confirmed=True,
        semantic_decode_confirmed=True,
    )


def _bulk_core_probe() -> ProbeMessage:
    return ProbeMessage(
        name=BULK_CORE_PROBE_NAME,
        tx=build_modbus_read_request(1, 0x03, 0x0000, 0x0031),
        expected_response=bytes([1, 0x03]),
        timeout_ms=2000,
        risk="safe_read",
        description="Source-confirmed PACE core read-only block registers 0x0000..0x0030.",
        slave_id=1,
        function_code=0x03,
        start_register=0x0000,
        quantity=0x0031,
        primary=False,
        hardware_confirmed=False,
    )


def _basic_block_probe() -> ProbeMessage:
    return _with_probe_metadata(
        ProbeMessage(
            name=BASIC_BLOCK_PROBE_NAME,
            tx=build_modbus_read_request(1, 0x03, 0x0000, 3),
            expected_response=bytes([1, 0x03]),
            timeout_ms=2000,
            risk="safe_read",
            description="Source-confirmed PACE basic block: current, pack voltage, SOC.",
            slave_id=1,
            function_code=0x03,
            start_register=0x0000,
            quantity=3,
            primary=False,
            hardware_confirmed=True,
        ),
        modbus_frame_confirmed=True,
        semantic_decode_confirmed=True,
    )


def _cell8_probe() -> ProbeMessage:
    return _with_probe_metadata(
        ProbeMessage(
            name=CELL8_PROBE_NAME,
            tx=build_modbus_read_request(1, 0x03, 0x0015, 8),
            expected_response=bytes([1, 0x03]),
            timeout_ms=2000,
            risk="safe_read",
            description="Source-confirmed PACE first 8 cell voltage registers.",
            slave_id=1,
            function_code=0x03,
            start_register=0x0015,
            quantity=8,
            primary=False,
            hardware_confirmed=True,
        ),
        modbus_frame_confirmed=True,
        semantic_decode_confirmed=False,
        decode_status="frame_valid_semantics_untrusted",
        warning=CELL8_SEMANTIC_WARNING,
    )


def _cell16_probe() -> ProbeMessage:
    return _with_probe_metadata(
        ProbeMessage(
            name=CELL16_PROBE_NAME,
            tx=build_modbus_read_request(1, 0x03, 0x0015, 16),
            expected_response=bytes([1, 0x03]),
            timeout_ms=2000,
            risk="safe_read",
            description="Source-confirmed PACE first 16 cell voltage registers.",
            slave_id=1,
            function_code=0x03,
            start_register=0x0015,
            quantity=16,
            primary=False,
            hardware_confirmed=True,
        ),
        modbus_frame_confirmed=True,
        semantic_decode_confirmed=False,
        decode_status="frame_valid_semantics_untrusted",
        warnings=("non_trailing_zero_cell_voltage", "cell_voltage_out_of_expected_range"),
    )


class PaceRs485ModbusV13Profile(ProtocolProfile):
    status = "active_safe_read_basic_block_hardware_confirmed_cell_frames_untrusted"
    research_status = status
    family = "pace"
    protocol_class = "modbus_rtu"
    default_baud_candidates = [9600]
    serial_format = "8N1"
    risk_policy = "safe_read_only"
    decode = "minimal_confirmed_decode"
    hardware_status = "hardware_confirmed_basic_block_cell_frames_untrusted"
    hardware_confirmed = True
    source_status = "source_confirmed_pdf"
    source_reference = CONFIRMED_SOURCE
    confirmed_bms_menu = CONFIRMED_BMS_MENU
    confirmed_serial = CONFIRMED_SERIAL
    confirmed_probe = SOURCE_PROBE_NAME
    confirmed_tx_hex = SOURCE_TX_HEX
    confirmed_rx_hex = CONFIRMED_RX_HEX
    source_confirmed_probe = SOURCE_PROBE_NAME
    source_confirmed_tx_hex = SOURCE_TX_HEX
    source_confirmed_bulk_probe = BULK_CORE_PROBE_NAME
    source_confirmed_bulk_tx_hex = BULK_CORE_TX_HEX
    bulk_core_block_hardware_confirmed = False
    bulk_core_block_hardware_result = "modbus_exception_code_02"
    bulk_core_block_exception_rx_hex = BULK_CORE_EXCEPTION_RX_HEX
    chunked_probe_names = (
        BASIC_BLOCK_PROBE_NAME,
        CELL8_PROBE_NAME,
        CELL16_PROBE_NAME,
    )
    basic_block_hardware_confirmed = True
    basic_block_semantic_decode_confirmed = True
    basic_block_confirmed_rx_hex = BASIC_BLOCK_CONFIRMED_RX_HEX
    cell8_hardware_confirmed = True
    cell8_modbus_frame_confirmed = True
    cell8_semantic_decode_confirmed = False
    cell8_decode_status = "frame_valid_semantics_untrusted"
    cell8_warning = CELL8_SEMANTIC_WARNING
    cell8_confirmed_rx_hex = CELL8_CONFIRMED_RX_HEX
    cell16_hardware_confirmed = True
    cell16_modbus_frame_confirmed = True
    cell16_semantic_decode_confirmed = False
    cell16_hardware_result = "confirmed_frame_with_decode_warnings"
    cell16_decode_status = "frame_valid_semantics_untrusted"
    cell16_warnings = ("non_trailing_zero_cell_voltage", "cell_voltage_out_of_expected_range")
    cell16_confirmed_rx_hex = CELL16_CONFIRMED_RX_HEX
    register_name = "pack_voltage"
    raw_type = "UINT16"
    unit = "10mV"
    allowed_function_codes = ALLOWED_FUNCTION_CODES
    forbidden_function_codes = FORBIDDEN_FUNCTION_CODES
    menu_mode = "004 PACE_RS485_Modbus_V1.3"

    def __init__(self) -> None:
        super().__init__(
            id=PROFILE_ID,
            name="PACE RS485 Modbus V1.3",
            transport="rs485",
            serial_candidates=[SerialSettings(baudrate=9600, parity="N")],
            probes=[
                _pack_voltage_probe(),
                _basic_block_probe(),
                _cell8_probe(),
                _cell16_probe(),
                _bulk_core_probe(),
            ],
            confidence_hint=50,
            enabled_by_default=True,
            primary_probe_names=(SOURCE_PROBE_NAME,),
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        return [rx_buffer] if len(rx_buffer) >= 5 else []

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        score = 0
        reasons: list[str] = []

        if len(frame) < 5:
            return ValidationResult(False, -50, ["short_modbus_frame"], self.decode_response(frame))

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
        decoded = self.decode_response(frame)
        if ok and self._is_confirmed_pack_voltage_probe(request, frame):
            raw_value = int.from_bytes(frame[3:5], byteorder="big")
            decoded.update(
                {
                    "parse_status": "decoded",
                    "decode_status": "hardware_confirmed_pack_voltage",
                    "register_0x0001_raw": raw_value,
                    "pack_voltage_v": round(raw_value * 0.01, 2),
                }
            )
            reasons.append("decoded_pack_voltage_ok")
            score += 10
        elif ok and self._is_bulk_core_probe(request, frame):
            decoded.update(self._decode_bulk_core_block(frame))
            reasons.append("decoded_bulk_core_block_ok")
            score += 10
        elif ok and self._is_basic_block_probe(request, frame):
            decoded.update(self._decode_basic_block(frame))
            reasons.append("decoded_basic_block_ok")
            score += 10
        elif ok and self._is_cell_voltage_probe(request, frame):
            decoded.update(self._decode_cell_voltage_block(request, frame))
            reasons.append("cell_voltage_frame_valid_semantics_untrusted")
            score += 10
        return ValidationResult(ok=ok, score_delta=score, reasons=reasons, decoded=decoded)

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

    @staticmethod
    def _is_confirmed_pack_voltage_probe(request: ProbeMessage, frame: bytes) -> bool:
        return (
            request.name == SOURCE_PROBE_NAME
            and request.slave_id == 1
            and request.function_code == 0x03
            and request.start_register == 0x0001
            and request.quantity == 1
            and len(frame) == 7
            and frame[2] == 2
        )

    @staticmethod
    def _is_bulk_core_probe(request: ProbeMessage, frame: bytes) -> bool:
        return (
            request.name == BULK_CORE_PROBE_NAME
            and request.slave_id == 1
            and request.function_code == 0x03
            and request.start_register == 0x0000
            and request.quantity == 0x0031
            and len(frame) == 103
            and frame[2] == 0x62
        )

    @staticmethod
    def _is_basic_block_probe(request: ProbeMessage, frame: bytes) -> bool:
        return (
            request.name == BASIC_BLOCK_PROBE_NAME
            and request.slave_id == 1
            and request.function_code == 0x03
            and request.start_register == 0x0000
            and request.quantity == 3
            and len(frame) == 11
            and frame[2] == 0x06
        )

    @staticmethod
    def _is_cell_voltage_probe(request: ProbeMessage, frame: bytes) -> bool:
        return (
            request.name in {CELL8_PROBE_NAME, CELL16_PROBE_NAME}
            and request.slave_id == 1
            and request.function_code == 0x03
            and request.start_register == 0x0015
            and request.quantity in {8, 16}
            and len(frame) == (request.quantity * 2) + 5
            and frame[2] == request.quantity * 2
        )

    @staticmethod
    def _decode_bulk_core_block(frame: bytes) -> dict:
        data = frame[3:-2]
        registers = [
            int.from_bytes(data[offset : offset + 2], byteorder="big")
            for offset in range(0, len(data), 2)
        ]
        raw_registers = {
            f"0x{index:04X}": value for index, value in enumerate(registers)
        }
        current_raw_signed = int.from_bytes(data[0:2], byteorder="big", signed=True)
        pack_voltage_raw = registers[0x0001]
        soc_raw = registers[0x0002]
        raw_only_notes: list[str] = []

        soc_percent = soc_raw if 0 <= soc_raw <= 100 else None
        if soc_percent is None:
            raw_only_notes.append("soc_raw_out_of_range")

        cell_start = 0x0015
        cell_values = registers[cell_start : 0x0030 + 1]
        unused_possible = [
            {
                "cell": index + 1,
                "register": f"0x{cell_start + index:04X}",
                "status": "unused_possible",
            }
            for index, value in enumerate(cell_values)
            if value == 0
        ]
        decode_warnings = PaceRs485ModbusV13Profile._cell_voltage_decode_warnings(cell_values)
        if CELL8_SEMANTIC_WARNING not in decode_warnings:
            decode_warnings.insert(0, CELL8_SEMANTIC_WARNING)

        decoded = {
            "parse_status": "decoded",
            "decode_status": "hardware_bulk_core_block",
            "slave_id": frame[0],
            "function_code": frame[1],
            "start_register": 0,
            "quantity": len(registers),
            "registers_raw": raw_registers,
            "current_raw_signed": current_raw_signed,
            "current_a": round(current_raw_signed * 0.01, 2),
            "pack_voltage_raw": pack_voltage_raw,
            "pack_voltage_v": round(pack_voltage_raw * 0.01, 2),
            "soc_percent_raw": soc_raw,
            "soc_percent": soc_percent,
            "cell_voltage_decode_status": "frame_valid_semantics_untrusted",
            "cell_voltage_semantic_decode_confirmed": False,
            "raw_candidate_cell_voltages_mv": cell_values,
            "unused_cell_registers_possible": unused_possible,
            "raw_registers_note": "Registers 0x0003..0x0014 are intentionally not field-decoded.",
        }
        if raw_only_notes:
            decoded["raw_only_notes"] = raw_only_notes
        if decode_warnings:
            decoded["decode_warnings"] = decode_warnings
        return decoded

    @staticmethod
    def _decode_basic_block(frame: bytes) -> dict:
        data = frame[3:-2]
        current_raw_signed = int.from_bytes(data[0:2], byteorder="big", signed=True)
        pack_voltage_raw = int.from_bytes(data[2:4], byteorder="big")
        soc_raw = int.from_bytes(data[4:6], byteorder="big")
        soc_percent = soc_raw if 0 <= soc_raw <= 100 else None
        decoded = {
            "parse_status": "decoded",
            "decode_status": "hardware_basic_block",
            "slave_id": frame[0],
            "function_code": frame[1],
            "start_register": 0,
            "quantity": 3,
            "registers_raw": {
                "0x0000": int.from_bytes(data[0:2], byteorder="big"),
                "0x0001": pack_voltage_raw,
                "0x0002": soc_raw,
            },
            "current_raw_signed": current_raw_signed,
            "current_a": round(current_raw_signed * 0.01, 2),
            "pack_voltage_raw": pack_voltage_raw,
            "pack_voltage_v": round(pack_voltage_raw * 0.01, 2),
            "soc_percent_raw": soc_raw,
            "soc_percent": soc_percent,
        }
        if soc_percent is None:
            decoded["raw_only_notes"] = ["soc_raw_out_of_range"]
        return decoded

    @staticmethod
    def _decode_cell_voltage_block(request: ProbeMessage, frame: bytes) -> dict:
        data = frame[3:-2]
        cell_values = [
            int.from_bytes(data[offset : offset + 2], byteorder="big")
            for offset in range(0, len(data), 2)
        ]
        unused_possible = [
            {
                "cell": index + 1,
                "register": f"0x{0x0015 + index:04X}",
                "status": "unused_possible",
            }
            for index, value in enumerate(cell_values)
            if value == 0
        ]
        decode_warnings = PaceRs485ModbusV13Profile._cell_voltage_decode_warnings(cell_values)
        if request.name == CELL8_PROBE_NAME and CELL8_SEMANTIC_WARNING not in decode_warnings:
            decode_warnings.insert(0, CELL8_SEMANTIC_WARNING)
        decoded = {
            "parse_status": "decoded",
            "decode_status": "frame_valid_semantics_untrusted",
            "slave_id": frame[0],
            "function_code": frame[1],
            "start_register": 0x0015,
            "quantity": request.quantity,
            "modbus_frame_confirmed": True,
            "semantic_decode_confirmed": False,
            "raw_candidate_cell_voltages_mv": cell_values,
            "unused_cell_registers_possible": unused_possible,
        }
        for index, value in enumerate(cell_values, start=1):
            decoded[f"raw_candidate_cell_{index:02d}_mv"] = value
        if decode_warnings:
            decoded["decode_warnings"] = decode_warnings
        return decoded

    @staticmethod
    def _cell_voltage_decode_warnings(cell_values: list[int]) -> list[str]:
        warnings: list[str] = []
        seen_zero = False
        non_trailing_zero = False
        out_of_range: list[dict] = []
        for index, value in enumerate(cell_values, start=1):
            if value == 0:
                seen_zero = True
                continue
            if seen_zero:
                non_trailing_zero = True
            if not MIN_PLAUSIBLE_CELL_MV <= value <= MAX_PLAUSIBLE_CELL_MV:
                out_of_range.append({"cell": index, "value_mv": value})
        if non_trailing_zero:
            warnings.append("non_trailing_zero_cell_voltage")
        if out_of_range:
            warnings.append("cell_voltage_out_of_expected_range")
        return warnings
