from __future__ import annotations

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile
from protocols.modbus_rtu import build_modbus_read_request, verify_crc

PROFILE_ID = "growatt_bms_rs485_1xsxxp"
SOURCE_REFERENCE = "Growatt_BMS_RS485_Protocol_1xSxxP_ESS_Rev2.01 / V2.02"
SOURCE_URL = "https://www.amosplanet.org/wp-content/uploads/2022/04/Growatt_BMS_RS485_protocal_1xSxxP_ESS_V2.02-1.pdf"
SOURCE_SERIAL = "9600 8N1"
SOURCE_MENU = "006 Growatt_BMS_RS485_Protocol_1x..."
PROBE_NAME = "read_soc_addr1"
SOURCE_TX_HEX = "01 03 00 15 00 01 95 CE"
CONFIRMED_RX_HEX = "01 03 02 00 42 38 75"
CONFIRMED_SERIAL = "9600 8N1"
CONFIRMED_BMS_MENU = SOURCE_MENU
STATUS_BLOCK_PROBE_NAME = "read_status_block_0x0013_0x0018_addr1"
STATUS_BLOCK_TX_HEX = "01 03 00 13 00 06 34 0D"
STATUS_BLOCK_CONFIRMED_RX_HEX = "01 03 0C 04 69 00 00 00 42 0A 47 00 00 00 14 64 8C"
CELL8_PROBE_NAME = "read_cell_voltages_1_8_addr1"
CELL8_TX_HEX = "01 03 00 71 00 08 14 17"
CELL8_CONFIRMED_RX_HEX = "01 03 10 0C D9 0C D9 0C DA 0C DA 0C D9 0C DA 0C DA 00 00 5F 2F"
CELL16_PROBE_NAME = "read_cell_voltages_1_16_addr1"
CELL16_TX_HEX = "01 03 00 71 00 10 14 1D"
CELL16_CONFIRMED_RX_HEX = (
    "01 03 20 0C D9 0C DA 0C DA 0C D9 0C D9 0C DA 0C DA 00 00 00 00 00 00 "
    "00 00 00 00 00 00 00 00 00 00 00 00 E9 96"
)
ALLOWED_FUNCTION_CODES = (0x03,)
FORBIDDEN_FUNCTION_CODES = (0x05, 0x06, 0x0F, 0x10)
MIN_PLAUSIBLE_CELL_MV = 2500
MAX_PLAUSIBLE_CELL_MV = 4500
CONFIRMED_STATUS_BLOCK_PACK_VOLTAGE_V = 26.31
CELL_SUM_MISMATCH_THRESHOLD_V = 1.0


def _with_probe_metadata(probe: ProbeMessage, **metadata) -> ProbeMessage:
    for key, value in metadata.items():
        setattr(probe, key, value)
    return probe


def _read_probe(
    *,
    name: str,
    start_register: int,
    quantity: int,
    description: str,
    primary: bool = False,
    hardware_confirmed: bool = False,
    semantic_decode_confirmed: bool | None = None,
) -> ProbeMessage:
    return _with_probe_metadata(
        ProbeMessage(
            name=name,
            tx=build_modbus_read_request(1, 0x03, start_register, quantity),
            expected_response=bytes([1, 0x03]),
            timeout_ms=2000,
            risk="safe_read",
            description=description,
            slave_id=1,
            function_code=0x03,
            start_register=start_register,
            quantity=quantity,
            primary=primary,
            hardware_confirmed=hardware_confirmed,
        ),
        source_confirmed=True,
        modbus_frame_confirmed=hardware_confirmed,
        semantic_decode_confirmed=(
            hardware_confirmed if semantic_decode_confirmed is None else semantic_decode_confirmed
        ),
        expected_byte_count=quantity * 2,
    )


class GrowattBmsRs4851xSxxpProfile(ProtocolProfile):
    status = "active_safe_read_status_block_hardware_confirmed_cell_frames_suspicious"
    research_status = status
    family = "growatt"
    protocol_class = "modbus_rtu"
    default_baud_candidates = [9600]
    serial_format = "8N1"
    risk_policy = "safe_read_only"
    decode = "minimal_confirmed_soc"
    hardware_status = "hardware_confirmed_status_block_cell_frames_semantics_suspicious"
    hardware_confirmed = True
    source_status = "source_confirmed_pdf"
    source_reference = SOURCE_REFERENCE
    source_url = SOURCE_URL
    bms_menu = SOURCE_MENU
    source_serial = SOURCE_SERIAL
    confirmed_bms_menu = CONFIRMED_BMS_MENU
    confirmed_serial = CONFIRMED_SERIAL
    confirmed_probe = PROBE_NAME
    confirmed_tx_hex = SOURCE_TX_HEX
    confirmed_rx_hex = CONFIRMED_RX_HEX
    source_confirmed_probe = PROBE_NAME
    source_confirmed_tx_hex = SOURCE_TX_HEX
    source_confirmed_block_probes = (
        STATUS_BLOCK_PROBE_NAME,
        CELL8_PROBE_NAME,
        CELL16_PROBE_NAME,
    )
    status_block_hardware_confirmed = True
    status_block_confirmed_tx_hex = STATUS_BLOCK_TX_HEX
    status_block_confirmed_rx_hex = STATUS_BLOCK_CONFIRMED_RX_HEX
    cell8_hardware_confirmed = True
    cell8_modbus_frame_confirmed = True
    cell8_semantic_decode_confirmed = False
    cell8_decode_status = "frame_valid_semantics_suspicious"
    cell8_confirmed_tx_hex = CELL8_TX_HEX
    cell8_confirmed_rx_hex = CELL8_CONFIRMED_RX_HEX
    cell16_hardware_confirmed = True
    cell16_modbus_frame_confirmed = True
    cell16_semantic_decode_confirmed = False
    cell16_decode_status = "frame_valid_semantics_suspicious"
    cell16_confirmed_tx_hex = CELL16_TX_HEX
    cell16_confirmed_rx_hex = CELL16_CONFIRMED_RX_HEX
    register_name = "soc"
    register_address = 0x0015
    raw_type = "UINT16"
    unit = "%"
    allowed_function_codes = ALLOWED_FUNCTION_CODES
    forbidden_function_codes = FORBIDDEN_FUNCTION_CODES

    def __init__(self) -> None:
        super().__init__(
            id=PROFILE_ID,
            name="Growatt BMS RS485 1xSxxP ESS safe-read",
            transport="rs485",
            serial_candidates=[SerialSettings(baudrate=9600, parity="N")],
            probes=[
                _read_probe(
                    name=PROBE_NAME,
                    start_register=0x0015,
                    quantity=1,
                    description=(
                        "Source-derived Growatt BMS RS485 SOC read, register 0x0015, "
                        "one holding register."
                    ),
                    primary=True,
                    hardware_confirmed=True,
                ),
                _read_probe(
                    name=STATUS_BLOCK_PROBE_NAME,
                    start_register=0x0013,
                    quantity=6,
                    description=(
                        "Source-derived Growatt BMS status block registers "
                        "0x0013..0x0018: status, error, SOC, voltage, current, temperature."
                    ),
                    hardware_confirmed=True,
                ),
                _read_probe(
                    name=CELL8_PROBE_NAME,
                    start_register=0x0071,
                    quantity=8,
                    description=(
                        "Source-derived Growatt BMS first 8 cell voltage registers "
                        "0x0071..0x0078."
                    ),
                    hardware_confirmed=True,
                    semantic_decode_confirmed=False,
                ),
                _read_probe(
                    name=CELL16_PROBE_NAME,
                    start_register=0x0071,
                    quantity=16,
                    description=(
                        "Source-derived Growatt BMS first 16 cell voltage registers "
                        "0x0071..0x0080."
                    ),
                    hardware_confirmed=True,
                    semantic_decode_confirmed=False,
                ),
            ],
            confidence_hint=45,
            enabled_by_default=True,
            primary_probe_names=(PROBE_NAME,),
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
        if ok and self._is_confirmed_soc_probe(request, frame):
            decoded.update(self._decode_confirmed_soc(frame))
            reasons.append("decoded_soc_ok")
            score += 10
        elif ok and self._is_status_block_probe(request, frame):
            decoded.update(self._decode_status_block(request, frame))
            reasons.append("decoded_status_block_ok")
            score += 10
        elif ok and self._is_cell_voltage_block_probe(request, frame):
            decoded.update(self._decode_cell_voltage_block(request, frame))
            reasons.append("cell_voltage_frame_valid_semantics_suspicious")
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
    def _is_confirmed_soc_probe(request: ProbeMessage, frame: bytes) -> bool:
        return (
            request.name == PROBE_NAME
            and request.slave_id == 1
            and request.function_code == 0x03
            and request.start_register == 0x0015
            and request.quantity == 1
            and len(frame) == 7
            and frame[2] == 2
        )

    @staticmethod
    def _decode_confirmed_soc(frame: bytes) -> dict:
        raw_value = int.from_bytes(frame[3:5], byteorder="big")
        decoded = {
            "parse_status": "decoded",
            "decode_status": "hardware_confirmed_single_register",
            "register_0x0015_raw": raw_value,
            "soc_raw": raw_value,
            "soc_percent_raw": raw_value,
            "soc_percent": raw_value if 0 <= raw_value <= 100 else None,
        }
        if decoded["soc_percent"] is None:
            decoded["raw_only_notes"] = ["soc_raw_out_of_range"]
        return decoded

    @staticmethod
    def _is_status_block_probe(request: ProbeMessage, frame: bytes) -> bool:
        return (
            request.name == STATUS_BLOCK_PROBE_NAME
            and request.slave_id == 1
            and request.function_code == 0x03
            and request.start_register == 0x0013
            and request.quantity == 6
            and len(frame) == 17
            and frame[2] == 12
        )

    @staticmethod
    def _is_cell_voltage_block_probe(request: ProbeMessage, frame: bytes) -> bool:
        return (
            request.name in {CELL8_PROBE_NAME, CELL16_PROBE_NAME}
            and request.slave_id == 1
            and request.function_code == 0x03
            and request.start_register == 0x0071
            and request.quantity in {8, 16}
            and len(frame) == (request.quantity * 2) + 5
            and frame[2] == request.quantity * 2
        )

    @staticmethod
    def _decode_status_block(request: ProbeMessage, frame: bytes) -> dict:
        data = frame[3:-2]
        registers = [
            int.from_bytes(data[offset : offset + 2], byteorder="big")
            for offset in range(0, len(data), 2)
        ]
        status_raw, error_raw, soc_raw, pack_voltage_raw, current_raw, temperature_raw = registers
        current_raw_signed = int.from_bytes(data[8:10], byteorder="big", signed=True)
        temperature_raw_signed = int.from_bytes(data[10:12], byteorder="big", signed=True)
        soc_percent = soc_raw if 0 <= soc_raw <= 100 else None
        decoded = {
            "parse_status": "decoded",
            "decode_status": (
                "hardware_confirmed_status_block"
                if request.hardware_confirmed
                else "source_confirmed_status_block"
            ),
            "slave_id": frame[0],
            "function_code": frame[1],
            "start_register": 0x0013,
            "quantity": 6,
            "registers_raw": {
                "0x0013": status_raw,
                "0x0014": error_raw,
                "0x0015": soc_raw,
                "0x0016": pack_voltage_raw,
                "0x0017": current_raw,
                "0x0018": temperature_raw,
            },
            "status_raw": status_raw,
            "error_raw": error_raw,
            "soc_raw": soc_raw,
            "soc_percent": soc_percent,
            "pack_voltage_raw": pack_voltage_raw,
            "pack_voltage_v": round(pack_voltage_raw * 0.01, 2),
            "current_raw": current_raw,
            "current_raw_signed": current_raw_signed,
            "current_a": round(current_raw_signed * 0.01, 2),
            "temperature_raw": temperature_raw,
            "temperature_raw_signed": temperature_raw_signed,
            "temperature_c": temperature_raw_signed,
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
        seen_zero = False
        non_trailing_zero = False
        candidate_active_values: list[int] = []
        out_of_range: list[dict[str, int]] = []
        unused_possible: list[dict[str, int | str]] = []
        for index, value in enumerate(cell_values, start=1):
            register = 0x0070 + index
            if value == 0:
                seen_zero = True
                unused_possible.append(
                    {"cell": index, "register": f"0x{register:04X}", "status": "unused_possible"}
                )
                continue
            if seen_zero:
                non_trailing_zero = True
            if MIN_PLAUSIBLE_CELL_MV <= value <= MAX_PLAUSIBLE_CELL_MV:
                candidate_active_values.append(value)
            else:
                out_of_range.append({"cell": index, "register": register, "value_mv": value})

        warnings: list[str] = []
        if non_trailing_zero:
            warnings.append("non_trailing_zero_cell_voltage")
        if out_of_range:
            warnings.append("cell_voltage_out_of_expected_range")

        candidate_sum_v = round(sum(candidate_active_values) / 1000, 3)
        expected_count = None
        if candidate_active_values:
            average_cell_v = sum(candidate_active_values) / len(candidate_active_values) / 1000
            expected_count = round(CONFIRMED_STATUS_BLOCK_PACK_VOLTAGE_V / average_cell_v)
            if abs(CONFIRMED_STATUS_BLOCK_PACK_VOLTAGE_V - candidate_sum_v) > CELL_SUM_MISMATCH_THRESHOLD_V:
                warnings.append("cell_sum_mismatch_pack_voltage")
            if expected_count != len(candidate_active_values):
                warnings.append("active_cell_count_mismatch_pack_voltage")

        decoded = {
            "parse_status": "decoded",
            "decode_status": "frame_valid_semantics_suspicious",
            "slave_id": frame[0],
            "function_code": frame[1],
            "start_register": 0x0071,
            "quantity": request.quantity,
            "modbus_frame_confirmed": request.hardware_confirmed,
            "semantic_decode_confirmed": False,
            "raw_candidate_cell_voltages_mv": cell_values,
            "raw_candidate_active_cell_voltages_mv": candidate_active_values,
            "raw_candidate_active_cell_count": len(candidate_active_values),
            "raw_candidate_cell_sum_v": candidate_sum_v,
            "reference_pack_voltage_v": CONFIRMED_STATUS_BLOCK_PACK_VOLTAGE_V,
            "unused_cell_registers_possible": unused_possible,
        }
        if expected_count is not None:
            decoded["expected_cell_count_from_pack_voltage"] = expected_count
        for index, value in enumerate(cell_values, start=1):
            decoded[f"raw_candidate_cell_{index:02d}_mv"] = value
        if out_of_range:
            decoded["out_of_range_cell_voltage_registers"] = out_of_range
        if warnings:
            decoded["decode_warnings"] = warnings
        return decoded
