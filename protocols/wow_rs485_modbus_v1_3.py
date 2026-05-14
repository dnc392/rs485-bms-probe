from __future__ import annotations

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile
from protocols.modbus_rtu import build_modbus_read_request, verify_crc

PROFILE_ID = "wow_rs485_modbus_v1_3"
SOURCE_MENU = "009 WOW_RS485_Modbus_V1.3"
EXPERIMENTAL_PROBE_ID = "experimental_read_reg_0x0001_qty1_addr1"
EXPERIMENTAL_REQUEST_HEX = "01 03 00 01 00 01 D5 CA"
EXPERIMENTAL_OBSERVED_RESPONSE_HEX = "01 03 02 0A 46 3F 16"
EXPERIMENTAL_BLOCK_PROBE_ID = "experimental_read_basic_block_0x0000_0x0002_addr1"
EXPERIMENTAL_BLOCK_REQUEST_HEX = "01 03 00 00 00 03 05 CB"
EXPERIMENTAL_BLOCK_OBSERVED_RESPONSE_HEX = "01 03 06 00 00 0A 46 00 42 43 49"
EXPERIMENTAL_CELL_PROBE_ID = "experimental_read_cell_voltages_0_7_addr1"
EXPERIMENTAL_CELL_REQUEST_HEX = "01 03 00 15 00 08 55 C8"
EXPERIMENTAL_CELL_OBSERVED_RESPONSE_HEX = (
    "01 03 10 0C D9 0C D7 00 00 00 00 00 00 00 00 00 00 00 00 C0 DC"
)
CANDIDATE_PACK_VOLTAGE_V = 26.30
FORBIDDEN_FUNCTION_CODES = {0x05, 0x06, 0x0F, 0x10}


def _experimental_probe() -> ProbeMessage:
    probe = ProbeMessage(
        name=EXPERIMENTAL_PROBE_ID,
        tx=build_modbus_read_request(
            slave_id=1,
            function_code=0x03,
            start_register=0x0001,
            quantity=1,
        ),
        expected_response=None,
        timeout_ms=2000,
        risk="experimental_unverified_read",
        description=(
            "Experimental FC03 read of one register for WOW_RS485_Modbus_V1.3. "
            "Not source-confirmed."
        ),
        slave_id=1,
        function_code=0x03,
        start_register=0x0001,
        quantity=1,
        primary=False,
        hardware_confirmed=False,
    )
    probe.source_confirmed = False
    probe.enabled_by_default = False
    probe.requires_explicit_unverified_flag = True
    probe.expected_byte_count = 2
    probe.hardware_observed = True
    probe.hardware_confirmed_experimental = True
    probe.confirmed_tx_hex = EXPERIMENTAL_REQUEST_HEX
    probe.confirmed_rx_hex = EXPERIMENTAL_OBSERVED_RESPONSE_HEX
    probe.confirmed_classification = "experimental_modbus_response_valid"
    return probe


def _experimental_block_probe() -> ProbeMessage:
    probe = ProbeMessage(
        name=EXPERIMENTAL_BLOCK_PROBE_ID,
        tx=build_modbus_read_request(
            slave_id=1,
            function_code=0x03,
            start_register=0x0000,
            quantity=3,
        ),
        expected_response=None,
        timeout_ms=2000,
        risk="experimental_unverified_read",
        description=(
            "Experimental FC03 read of registers 0x0000..0x0002 for "
            "WOW_RS485_Modbus_V1.3. Not source-confirmed."
        ),
        slave_id=1,
        function_code=0x03,
        start_register=0x0000,
        quantity=3,
        primary=False,
        hardware_confirmed=False,
    )
    probe.source_confirmed = False
    probe.enabled_by_default = False
    probe.requires_explicit_unverified_flag = True
    probe.expected_byte_count = 6
    probe.expected_response_shape = "01 03 06 <6 data bytes> <crc_lo> <crc_hi>"
    probe.hardware_observed = True
    probe.hardware_confirmed_experimental = True
    probe.confirmed_tx_hex = EXPERIMENTAL_BLOCK_REQUEST_HEX
    probe.confirmed_rx_hex = EXPERIMENTAL_BLOCK_OBSERVED_RESPONSE_HEX
    probe.confirmed_classification = "experimental_modbus_response_valid"
    return probe


def _experimental_cell_probe() -> ProbeMessage:
    probe = ProbeMessage(
        name=EXPERIMENTAL_CELL_PROBE_ID,
        tx=build_modbus_read_request(
            slave_id=1,
            function_code=0x03,
            start_register=0x0015,
            quantity=8,
        ),
        expected_response=None,
        timeout_ms=2000,
        risk="experimental_unverified_read",
        description=(
            "Experimental FC03 read of cell-voltage candidate registers 0x0015..0x001C "
            "for WOW_RS485_Modbus_V1.3. Not source-confirmed."
        ),
        slave_id=1,
        function_code=0x03,
        start_register=0x0015,
        quantity=8,
        primary=False,
        hardware_confirmed=False,
    )
    probe.source_confirmed = False
    probe.enabled_by_default = False
    probe.requires_explicit_unverified_flag = True
    probe.expected_byte_count = 16
    probe.expected_response_shape = "01 03 10 <16 data bytes> <crc_lo> <crc_hi>"
    probe.hardware_observed = True
    probe.hardware_confirmed_experimental = True
    probe.confirmed_tx_hex = EXPERIMENTAL_CELL_REQUEST_HEX
    probe.confirmed_rx_hex = EXPERIMENTAL_CELL_OBSERVED_RESPONSE_HEX
    probe.confirmed_classification = "experimental_modbus_response_valid"
    probe.frame_valid = True
    probe.semantic_confirmed = False
    probe.semantic_status = "frame_valid_semantics_failed"
    probe.failure_reason = "candidate_cell_sum_mismatch_pack_voltage"
    return probe


def _decode_candidate_cells(values: dict[int, int]) -> dict[str, object]:
    ordered = [values[register] for register in range(0x0015, 0x001D)]
    active = [value for value in ordered if value != 0]
    candidate_sum_v = round(sum(active) / 1000, 3)
    decoded: dict[str, object] = {
        "decode_status": "experimental_candidate_decode",
        "semantic_confirmed": False,
        "candidate_note": "Experimental unverified value; not source-confirmed.",
        "candidate_cell_voltages_mv": ordered,
        "candidate_active_cell_voltages_mv": active,
        "candidate_active_cell_count": len(active),
        "candidate_min_cell_mv": min(active) if active else None,
        "candidate_max_cell_mv": max(active) if active else None,
        "candidate_delta_cell_mv": (max(active) - min(active)) if active else None,
        "candidate_cell_sum_v": candidate_sum_v,
        "candidate_pack_voltage_reference_v": CANDIDATE_PACK_VOLTAGE_V,
    }
    if abs(candidate_sum_v - CANDIDATE_PACK_VOLTAGE_V) <= 1.0:
        decoded["candidate_info"] = ["candidate_cell_sum_matches_pack_voltage"]
        decoded["semantic_status"] = "frame_valid_semantics_unconfirmed"
    else:
        decoded["candidate_warnings"] = ["candidate_cell_sum_mismatch_pack_voltage"]
        decoded["semantic_status"] = "frame_valid_semantics_failed"
        decoded["failure_reason"] = "candidate_cell_sum_mismatch_pack_voltage"
    return decoded


def _decode_candidate_registers(request: ProbeMessage, data: bytes) -> dict[str, object]:
    decoded: dict[str, object] = {
        "semantic_confirmed": False,
        "candidate_note": "Experimental unverified value; not source-confirmed.",
    }
    start_register = request.start_register or 0
    values: dict[int, int] = {}
    for offset in range(0, len(data), 2):
        register = start_register + (offset // 2)
        value = int.from_bytes(data[offset : offset + 2], byteorder="big")
        values[register] = value
        decoded[f"candidate_register_0x{register:04X}_raw"] = value

    if request.start_register == 0x0015 and request.quantity == 8 and set(values) >= set(range(0x0015, 0x001D)):
        decoded.update(_decode_candidate_cells(values))
    elif set(values) >= {0x0000, 0x0001, 0x0002}:
        current_raw = values[0x0000]
        current_signed = current_raw - 0x10000 if current_raw & 0x8000 else current_raw
        candidate_current_a = current_signed * 0.01
        candidate_pack_voltage_v = values[0x0001] * 0.01
        soc_raw = values[0x0002]
        decoded["decode_status"] = "experimental_candidate_decode"
        decoded["candidate_current_a"] = round(candidate_current_a, 3)
        decoded["candidate_pack_voltage_v"] = round(candidate_pack_voltage_v, 3)
        if 0 <= soc_raw <= 100:
            decoded["candidate_soc_percent"] = soc_raw
        else:
            decoded["candidate_soc_percent"] = None
    else:
        decoded["decode_status"] = "experimental_modbus_response_valid"
    return decoded


def _raw_decode(
    *,
    frame: bytes,
    request: ProbeMessage,
    classification: str,
    crc_ok: bool,
    warnings: list[str] | None = None,
) -> dict:
    decoded: dict[str, object] = {
        "parse_status": "raw_only",
        "classification": classification,
        "crc_status": "verified" if crc_ok else "invalid",
        "raw_hex": frame.hex(" ").upper(),
    }
    if len(frame) >= 1:
        decoded["slave_id"] = frame[0]
    if len(frame) >= 2:
        decoded["function_code"] = frame[1]
    if len(frame) >= 3:
        decoded["byte_count"] = frame[2]
    if classification == "experimental_modbus_response_valid":
        data = frame[3:-2]
        decoded.update(
            {
                "frame_valid": True,
                "function_code": request.function_code,
                "byte_count": len(data),
                "data_hex": data.hex(" ").upper(),
            }
        )
        decoded.update(_decode_candidate_registers(request, data))
    if warnings:
        decoded["warnings"] = warnings
    return decoded


class WowRs485ModbusV13Profile(ProtocolProfile):
    status = "inactive_research_with_experimental_read"
    research_status = status
    family = "wow"
    protocol_class = "experimental_standard_modbus_rtu_assumption"
    default_baud_candidates = [9600]
    serial_format = "9600 8N1 experimental assumption"
    risk_policy = "explicit_experimental_unverified_read_only"
    decode = "raw_only"
    hardware_status = "unverified_hardware"
    hardware_confirmed = False
    hardware_observed = True
    hardware_confirmed_experimental = True
    experimental_observed_tx_hex = EXPERIMENTAL_REQUEST_HEX
    experimental_observed_rx_hex = EXPERIMENTAL_OBSERVED_RESPONSE_HEX
    experimental_observed_classification = "experimental_modbus_response_valid"
    experimental_block_observed_tx_hex = EXPERIMENTAL_BLOCK_REQUEST_HEX
    experimental_block_observed_rx_hex = EXPERIMENTAL_BLOCK_OBSERVED_RESPONSE_HEX
    experimental_block_observed_classification = "experimental_modbus_response_valid"
    experimental_cell_observed_tx_hex = EXPERIMENTAL_CELL_REQUEST_HEX
    experimental_cell_observed_rx_hex = EXPERIMENTAL_CELL_OBSERVED_RESPONSE_HEX
    experimental_cell_observed_classification = "experimental_modbus_response_valid"
    source_status = "missing_confirmed_safe_read_request"
    experimental_probe_count = 3
    bms_menu = SOURCE_MENU
    reason = "missing_confirmed_safe_read_request"
    source_notes = (
        "Compatibility lists mention WOW RS485 Modbus V1.3-2017.06.27, "
        "but no source document with frame format and a confirmed read-only request "
        "has been found. Probes are explicit experimental_unverified_read "
        "standard Modbus FC03 assumptions and are not used by scan/default activation."
    )

    def __init__(self) -> None:
        super().__init__(
            id=PROFILE_ID,
            name="WOW RS485 Modbus V1.3 research-only",
            transport="rs485",
            serial_candidates=[SerialSettings(baudrate=9600, parity="N")],
            probes=[_experimental_probe(), _experimental_block_probe(), _experimental_cell_probe()],
            confidence_hint=0,
            enabled_by_default=False,
            primary_probe_names=(),
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        return [rx_buffer] if rx_buffer else []

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        reasons: list[str] = []
        warnings: list[str] = []
        if not frame:
            return ValidationResult(
                ok=False,
                score_delta=-50,
                reasons=["experimental_no_response"],
                decoded={},
            )
        if frame == request.tx:
            return ValidationResult(
                ok=False,
                score_delta=-80,
                reasons=["echoed_request"],
                decoded=_raw_decode(
                    frame=frame,
                    request=request,
                    classification="experimental_unexpected_shape",
                    crc_ok=verify_crc(frame),
                    warnings=["echoed_request"],
                ),
            )
        reasons.append("not_echo")

        crc_ok = verify_crc(frame)
        if not crc_ok:
            return ValidationResult(
                ok=False,
                score_delta=-60,
                reasons=reasons + ["crc_invalid"],
                decoded=_raw_decode(
                    frame=frame,
                    request=request,
                    classification="experimental_invalid_crc",
                    crc_ok=False,
                ),
            )
        reasons.append("crc_ok")

        if len(frame) < 5:
            return ValidationResult(
                ok=False,
                score_delta=-40,
                reasons=reasons + ["short_modbus_frame"],
                decoded=_raw_decode(
                    frame=frame,
                    request=request,
                    classification="experimental_unexpected_shape",
                    crc_ok=True,
                ),
            )

        expected_slave = request.slave_id
        expected_function = request.function_code
        expected_byte_count = (request.quantity or 0) * 2

        if frame[0] != expected_slave:
            return ValidationResult(
                ok=False,
                score_delta=-40,
                reasons=reasons + ["slave_id_mismatch"],
                decoded=_raw_decode(
                    frame=frame,
                    request=request,
                    classification="experimental_unexpected_shape",
                    crc_ok=True,
                ),
            )
        reasons.append("slave_id_ok")

        if expected_function is not None and frame[1] == (expected_function | 0x80):
            exception_code = frame[2] if len(frame) >= 3 else 0
            return ValidationResult(
                ok=False,
                score_delta=-25,
                reasons=reasons + ["modbus_exception_response", f"exception_code_{exception_code:02X}"],
                decoded=_raw_decode(
                    frame=frame,
                    request=request,
                    classification="experimental_modbus_exception",
                    crc_ok=True,
                ),
            )

        if frame[1] != expected_function:
            return ValidationResult(
                ok=False,
                score_delta=-40,
                reasons=reasons + ["function_code_mismatch"],
                decoded=_raw_decode(
                    frame=frame,
                    request=request,
                    classification="experimental_unexpected_shape",
                    crc_ok=True,
                ),
            )
        reasons.append("function_code_ok")

        byte_count = frame[2]
        expected_length = 1 + 1 + 1 + expected_byte_count + 2
        if byte_count != expected_byte_count:
            if len(frame) == 8:
                warnings.append("request_shaped_or_custom_frame")
                reasons.append("experimental_unexpected_shape")
            return ValidationResult(
                ok=False,
                score_delta=-30,
                reasons=reasons + ["byte_count_mismatch"],
                decoded=_raw_decode(
                    frame=frame,
                    request=request,
                    classification="experimental_unexpected_shape",
                    crc_ok=True,
                    warnings=warnings,
                ),
            )
        if len(frame) != expected_length:
            return ValidationResult(
                ok=False,
                score_delta=-30,
                reasons=reasons + ["response_length_mismatch"],
                decoded=_raw_decode(
                    frame=frame,
                    request=request,
                    classification="experimental_unexpected_shape",
                    crc_ok=True,
                ),
            )
        reasons.append("byte_count_ok")

        return ValidationResult(
            ok=True,
            score_delta=85,
            reasons=reasons,
            decoded=_raw_decode(
                frame=frame,
                request=request,
                classification="experimental_modbus_response_valid",
                crc_ok=True,
            ),
        )
