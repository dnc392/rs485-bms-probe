from __future__ import annotations

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile
from protocols.modbus_rtu import build_modbus_read_request, verify_crc

PROFILE_ID = "voltronic_inverter_bms_485"
SOURCE_REFERENCE = "Voltronic Inverter and BMS 485 communication protocol 20201202"
SOURCE_URL = (
    "https://github.com/ardupic/voltronic-inverter-communication-protocols/"
    "blob/main/Voltronic%20Inverter%20and%20BMS%20485%20communication%20protocol%2020201202.docx"
)
SOURCE_SERIAL = "9600 8N1"
SOURCE_MENU = "007 Voltronic_Inverter_and_BMS_485-..."
PROBE_NAME = "read_cell_count_addr1"
SOURCE_TX_HEX = "01 03 00 10 00 01 85 CF"
OBSERVED_RX_HEX = "01 03 00 01 00 08 15 CC"
ALLOWED_FUNCTION_CODES = (0x03,)
FORBIDDEN_FUNCTION_CODES = (0x05, 0x06, 0x0F, 0x10)


def _source_probe() -> ProbeMessage:
    probe = ProbeMessage(
        name=PROBE_NAME,
        tx=build_modbus_read_request(1, 0x03, 0x0010, 1),
        expected_response=bytes([1, 0x03]),
        timeout_ms=2000,
        risk="safe_read",
        description=(
            "Source-derived Voltronic inverter/BMS 485 read of register 0x0010 "
            "Number of cell, one holding register."
        ),
        slave_id=1,
        function_code=0x03,
        start_register=0x0010,
        quantity=1,
        primary=True,
        hardware_confirmed=True,
    )
    setattr(probe, "source_confirmed", True)
    setattr(probe, "expected_byte_count", 2)
    setattr(probe, "standard_modbus_confirmed", False)
    setattr(probe, "source_custom_response_confirmed", True)
    setattr(probe, "confirmed_tx_hex", SOURCE_TX_HEX)
    setattr(probe, "confirmed_rx_hex", OBSERVED_RX_HEX)
    return probe


class VoltronicInverterBms485Profile(ProtocolProfile):
    status = "active_safe_read_single_probe_hardware_confirmed_source_custom"
    research_status = status
    family = "voltronic"
    protocol_class = "modbus_rtu_like"
    default_baud_candidates = [9600]
    serial_format = "8N1"
    risk_policy = "safe_read_only"
    decode = "minimal_confirmed_cell_count_source_custom"
    hardware_status = "hardware_confirmed_source_custom_single_probe"
    hardware_confirmed = True
    standard_modbus_confirmed = False
    source_custom_response_confirmed = True
    source_status = "source_confirmed_docx"
    source_reference = SOURCE_REFERENCE
    source_url = SOURCE_URL
    bms_menu = SOURCE_MENU
    source_serial = SOURCE_SERIAL
    source_confirmed_probe = PROBE_NAME
    source_confirmed_tx_hex = SOURCE_TX_HEX
    confirmed_probe = PROBE_NAME
    confirmed_tx_hex = SOURCE_TX_HEX
    confirmed_rx_hex = OBSERVED_RX_HEX
    confirmed_serial = SOURCE_SERIAL
    confirmed_bms_menu = SOURCE_MENU
    register_name = "number_of_cells"
    register_address = 0x0010
    raw_type = "UINT16"
    unit = "pcs"
    allowed_function_codes = ALLOWED_FUNCTION_CODES
    forbidden_function_codes = FORBIDDEN_FUNCTION_CODES

    def __init__(self) -> None:
        super().__init__(
            id=PROFILE_ID,
            name="Voltronic Inverter and BMS 485 safe-read",
            transport="rs485",
            serial_candidates=[SerialSettings(baudrate=9600, parity="N")],
            probes=[_source_probe()],
            confidence_hint=45,
            enabled_by_default=True,
            primary_probe_names=(PROBE_NAME,),
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        return [rx_buffer] if len(rx_buffer) >= 5 else []

    def _is_source_response_shape(self, request: ProbeMessage, frame: bytes) -> bool:
        if len(frame) < 8 or not verify_crc(frame):
            return False
        expected_quantity = request.quantity
        if expected_quantity is None and len(request.tx) >= 6:
            expected_quantity = int.from_bytes(request.tx[4:6], byteorder="big")
        data_length_words = int.from_bytes(frame[2:4], byteorder="big")
        data_bytes = frame[4:-2]
        return (
            expected_quantity is not None
            and data_length_words == expected_quantity
            and len(data_bytes) == data_length_words * 2
            and len(frame) == 6 + data_length_words * 2
        )

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
            reasons.append("voltronic_abnormal_response")
            if len(frame) >= 3:
                reasons.append(f"error_code_{frame[2]:02X}")
                reasons.append(f"exception_code_{frame[2]:02X}")
            score -= 50
        else:
            reasons.append("function_code_mismatch")
            score -= 50

        byte_count_ok = False
        if frame[1] == expected_function and len(frame) >= 5 and not is_exception:
            if len(frame) >= 6:
                data_length_words = int.from_bytes(frame[2:4], byteorder="big")
                data_bytes = frame[4:-2]
                length_ok = len(data_bytes) == data_length_words * 2 and len(frame) == 6 + data_length_words * 2
                expected_count_ok = expected_quantity is None or data_length_words == expected_quantity
            else:
                data_length_words = None
                length_ok = False
                expected_count_ok = False
            byte_count_ok = length_ok and expected_count_ok
            if byte_count_ok:
                reasons.append("voltronic_custom_data_length_ok")
                reasons.append("source_response_length_ok")
                reasons.append("source_custom_response_confirmed")
                if len(frame) == 8:
                    reasons.append("standard_modbus_request_shape_ambiguous")
                score += 10
            else:
                if not expected_count_ok:
                    reasons.append("data_length_mismatch")
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
                self._is_source_response_shape(request, frame),
            ]
        )
        return ValidationResult(ok=ok, score_delta=score, reasons=reasons, decoded=self.decode_response(frame, request))

    def decode_response(self, frame: bytes, request: ProbeMessage | None = None) -> dict:
        decoded = {
            "raw_hex": frame.hex(" ").upper(),
            "parse_status": "raw_only",
            "crc_status": "verified" if verify_crc(frame) else "invalid",
        }
        if len(frame) >= 5:
            source_data_length_words = int.from_bytes(frame[2:4], byteorder="big") if len(frame) >= 6 else None
            source_data_hex = frame[4:-2].hex(" ").upper() if len(frame) >= 6 else ""
            classification = "raw_only"
            if frame[1] in ALLOWED_FUNCTION_CODES and verify_crc(frame) and source_data_length_words is not None:
                expected_frame_length = 6 + source_data_length_words * 2
                if len(frame) == expected_frame_length:
                    classification = "source_custom_response_confirmed"
                elif len(frame) == 8:
                    classification = "valid_crc_unexpected_modbus_request_shape"
                else:
                    classification = "valid_crc_unexpected_response_length"
            elif len(frame) >= 3 and frame[1] == 0x83 and verify_crc(frame):
                classification = "voltronic_abnormal_response"
            decoded.update(
                {
                    "slave_id": frame[0],
                    "function_code": frame[1],
                    "byte_count": None,
                    "source_data_length_words": source_data_length_words,
                    "source_data_hex": source_data_hex,
                    "classification": classification,
                }
            )
            if (
                request is not None
                and request.name == PROBE_NAME
                and frame != request.tx
                and verify_crc(frame)
                and len(frame) == 8
                and frame[0] == 1
                and frame[1] == 0x03
                and source_data_length_words == 1
                and len(frame[4:-2]) == 2
            ):
                raw_value = int.from_bytes(frame[4:6], byteorder="big")
                decoded.update(
                    {
                        "parse_status": "decoded",
                        "protocol_shape": "voltronic_source_custom_response",
                        "command_type": 3,
                        "data_length_words": 1,
                        "data_bytes": frame[4:6].hex(" ").upper(),
                        "register_0x0010_raw": raw_value,
                        "cell_count": raw_value,
                        "decode_status": "hardware_confirmed_single_register_source_custom",
                        "warnings": [
                            "standard_modbus_request_shape_ambiguous",
                            "not_standard_modbus_response",
                        ],
                    }
                )
        return decoded
