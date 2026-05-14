from __future__ import annotations

import math

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

EXPECTED_PREFIX = b"~200246"
MAX_FRAME_BODY_HEX_LEN = 512
MIN_FRAME_BODY_HEX_LEN = len(b"200246000000")
CHECKSUM_HEX_LEN = 4
DEFAULT_SANITY_RANGES = {
    "pack_voltage_v": (5.0, 100.0),
    "cell_voltage_v": (1.5, 4.5),
    "cell_count": (4, 32),
    "soc_percent": (0, 100),
    "temperature_c": (-40.0, 100.0),
}
DECODED_UNITS = {
    "system_total_average_voltage_v": "V",
    "system_total_current_a": "A",
    "system_soc_percent": "%",
    "average_soh_percent": "%",
    "minimum_soh_percent": "%",
    "highest_cell_voltage_v": "V",
    "lowest_cell_voltage_v": "V",
    "average_cell_temperature_c": "C",
    "highest_cell_temperature_c": "C",
    "charge_voltage_limit_v": "V",
    "discharge_voltage_limit_v": "V",
    "charge_current_limit_a": "A",
    "discharge_current_limit_a": "A",
    "cell_count": "count",
}


def _probe(name: str, tx_ascii: str) -> ProbeMessage:
    return ProbeMessage(name=name, tx=tx_ascii.encode("ascii"), expected_response=EXPECTED_PREFIX, timeout_ms=500, risk="safe_read")


def _is_upper_hex(data: bytes) -> bool:
    return all(0x30 <= b <= 0x39 or 0x41 <= b <= 0x46 for b in data)


def calculate_pylon_checksum(frame_data: bytes) -> str:
    checksum = ((~sum(frame_data)) & 0xFFFF) + 1
    return f"{checksum & 0xFFFF:04X}"


def _checksum_parts(frame: bytes) -> tuple[bytes, str] | None:
    if not frame.startswith(b"~") or not frame.endswith(b"\r"):
        return None
    body = frame[1:-1]
    if len(body) < CHECKSUM_HEX_LEN:
        return None
    received = body[-CHECKSUM_HEX_LEN:]
    if len(received) != CHECKSUM_HEX_LEN or not _is_upper_hex(received):
        return None
    return body[:-CHECKSUM_HEX_LEN], received.decode("ascii")


def verify_pylon_checksum(frame: bytes) -> tuple[bool, str]:
    parts = _checksum_parts(frame)
    if parts is None:
        return False, "checksum_not_checked"
    frame_data, received = parts
    calculated = calculate_pylon_checksum(frame_data)
    return received == calculated, f"received={received} calculated={calculated}"


def _parse_frame_data(frame_data: bytes) -> dict:
    body = frame_data.decode("ascii")
    if len(body) < 12:
        return {"parse_status": "raw_only"}
    length_raw = body[8:12]
    try:
        length_value = int(length_raw, 16)
    except ValueError:
        return {"parse_status": "raw_only"}
    info_hex = body[12:]
    return {
        "version": body[0:2],
        "address": body[2:4],
        "cid1": body[4:6],
        "return_code": body[6:8],
        "length": length_raw,
        "info_length_ascii": length_value & 0x0FFF,
        "info_hex": info_hex,
        "length_matches_info": (length_value & 0x0FFF) == len(info_hex),
    }


def _u16(data: bytes) -> int:
    return int.from_bytes(data, byteorder="big", signed=False)


def _s16(data: bytes) -> int:
    return int.from_bytes(data, byteorder="big", signed=True)


def _kelvin10_to_celsius(raw: int) -> float:
    return round((raw - 2731) / 10.0, 1)


def _bit_flags(value: int, names: dict[int, str]) -> dict:
    return {
        "raw_hex": f"{value:02X}",
        "flags": {name: bool(value & (1 << bit)) for bit, name in names.items()},
        "unknown_bits": [bit for bit in range(7, -1, -1) if bit not in names],
    }


def _decode_0x62(info: bytes) -> dict:
    if len(info) < 4:
        return {"parse_status": "raw_only"}
    return {
        "parse_status": "partial",
        "response_type": "system_alarm_status",
        "system_alarm_status_1": _bit_flags(
            info[0],
            {
                7: "module_voltage_high_alarm",
                6: "module_voltage_low_alarm",
                5: "cell_voltage_high_alarm",
                4: "cell_voltage_low_alarm",
                3: "cell_temperature_high_alarm",
                2: "cell_temperature_low_alarm",
                1: "mosfet_temperature_high_alarm",
                0: "cell_voltage_consistency_alarm",
            },
        ),
        "system_alarm_status_2": _bit_flags(
            info[1],
            {
                7: "cell_temperature_consistency_alarm",
                6: "charge_overcurrent_alarm",
                5: "discharge_overcurrent_alarm",
                4: "internal_communication_error",
            },
        ),
        "system_protection_status_1": _bit_flags(
            info[2],
            {
                7: "module_voltage_overvoltage_protection",
                6: "module_voltage_undervoltage_protection",
                5: "cell_voltage_overvoltage_protection",
                4: "cell_voltage_undervoltage_protection",
                3: "cell_temperature_overtemperature_protection",
                2: "cell_temperature_undertemperature_protection",
                1: "mosfet_overtemperature_protection",
            },
        ),
        "system_protection_status_2": _bit_flags(
            info[3],
            {
                6: "charge_overcurrent_protection",
                5: "discharge_overcurrent_protection",
                3: "system_fault_protection",
            },
        ),
    }


def _decode_0x63(info: bytes) -> dict:
    if len(info) < 9:
        return {"parse_status": "raw_only"}
    status = info[8]
    return {
        "parse_status": "partial",
        "response_type": "charge_discharge_management",
        "charge_voltage_limit_v": round(_u16(info[0:2]) / 1000.0, 3),
        "discharge_voltage_limit_v": round(_u16(info[2:4]) / 1000.0, 3),
        "charge_current_limit_a": round(_s16(info[4:6]) / 10.0, 1),
        "discharge_current_limit_a": round(_s16(info[6:8]) / 10.0, 1),
        "charge_discharge_status": _bit_flags(
            status,
            {
                7: "charge_enable",
                6: "discharge_enable",
                5: "charge_immediately",
                4: "full_charge_request",
            },
        ),
    }


def _decode_0x61(info: bytes) -> dict:
    if len(info) < 25:
        return {"parse_status": "raw_only"}
    return {
        "parse_status": "partial",
        "response_type": "system_analog_data",
        "system_total_average_voltage_v": round(_u16(info[0:2]) / 1000.0, 3),
        "system_total_current_a": round(_s16(info[2:4]) / 100.0, 2),
        "system_soc_percent": info[4],
        "average_cycle_count": _u16(info[5:7]),
        "maximum_cycle_count": _u16(info[7:9]),
        "average_soh_percent": info[9],
        "minimum_soh_percent": info[10],
        "highest_cell_voltage_v": round(_u16(info[11:13]) / 1000.0, 3),
        "highest_cell_voltage_module_raw": info[13:15].hex().upper(),
        "lowest_cell_voltage_v": round(_u16(info[15:17]) / 1000.0, 3),
        "lowest_cell_voltage_module_raw": info[17:19].hex().upper(),
        "average_cell_temperature_c": _kelvin10_to_celsius(_s16(info[19:21])),
        "highest_cell_temperature_c": _kelvin10_to_celsius(_s16(info[21:23])),
        "highest_cell_temperature_module_raw": info[23:25].hex().upper(),
        "undecoded_tail_hex": info[25:].hex().upper(),
    }


def _decode_info(request: ProbeMessage, info: bytes) -> dict:
    if request.name == "read_system_alarm_info":
        return _decode_0x62(info)
    if request.name == "read_charge_discharge_management":
        return _decode_0x63(info)
    if request.name == "read_system_analog_data":
        return _decode_0x61(info)
    return {"parse_status": "raw_only"}


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _check_range(decoded: dict, key: str, low: float, high: float, warnings: list[str]) -> bool:
    if key not in decoded:
        return False
    value = decoded[key]
    if not _is_finite_number(value) or not low <= value <= high:
        warnings.append(f"{key}_out_of_range")
    return True


def apply_pylon_sanity(decoded: dict, ranges: dict | None = None) -> dict:
    ranges = DEFAULT_SANITY_RANGES if ranges is None else {**DEFAULT_SANITY_RANGES, **ranges}
    warnings: list[str] = []
    checked = 0

    pack_low, pack_high = ranges["pack_voltage_v"]
    for key in ("system_total_average_voltage_v", "charge_voltage_limit_v", "discharge_voltage_limit_v"):
        checked += int(_check_range(decoded, key, pack_low, pack_high, warnings))

    cell_low, cell_high = ranges["cell_voltage_v"]
    for key in ("highest_cell_voltage_v", "lowest_cell_voltage_v"):
        checked += int(_check_range(decoded, key, cell_low, cell_high, warnings))

    count_low, count_high = ranges["cell_count"]
    checked += int(_check_range(decoded, "cell_count", count_low, count_high, warnings))

    soc_low, soc_high = ranges["soc_percent"]
    for key in ("system_soc_percent",):
        checked += int(_check_range(decoded, key, soc_low, soc_high, warnings))

    temp_low, temp_high = ranges["temperature_c"]
    for key in ("average_cell_temperature_c", "highest_cell_temperature_c"):
        checked += int(_check_range(decoded, key, temp_low, temp_high, warnings))

    for key in ("system_total_current_a", "charge_current_limit_a", "discharge_current_limit_a"):
        if key not in decoded:
            continue
        checked += 1
        if not _is_finite_number(decoded[key]):
            warnings.append(f"{key}_not_finite")

    decoded["decoded_units"] = {
        key: unit for key, unit in DECODED_UNITS.items() if key in decoded
    }
    decoded["sanity_warnings"] = warnings
    if checked == 0:
        decoded["sanity_status"] = "not_applicable"
    elif warnings:
        decoded["sanity_status"] = "failed"
    else:
        decoded["sanity_status"] = "passed"
    return decoded


class PylonLvProfile(ProtocolProfile):
    def __init__(self, sanity_ranges: dict | None = None) -> None:
        self.sanity_ranges = sanity_ranges
        super().__init__(
            id="pylon_lv_rs485",
            name="Pylontech / Pylon LV RS485 ASCII",
            transport="rs485",
            serial_candidates=[SerialSettings(baudrate=9600, parity="N")],
            probes=[
                _probe("read_system_analog_data", "~201246610000FDAA\r"),
                _probe("read_system_alarm_info", "~201246620000FDA9\r"),
                _probe("read_charge_discharge_management", "~201246630000FDA8\r"),
            ],
            confidence_hint=95,
            primary_probe_names=("read_system_analog_data",),
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        frames: list[bytes] = []
        for chunk in rx_buffer.split(b"\r"):
            start = chunk.find(b"~")
            if start >= 0:
                candidate = chunk[start:]
                if candidate:
                    frames.append(candidate + b"\r")
        return frames

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        score = 0
        reasons: list[str] = []

        frame_start_ok = frame.startswith(b"~")
        if frame_start_ok:
            score += 5
            reasons.append("frame_start_ok")
        else:
            score -= 50
            reasons.append("frame_start_missing")

        frame_end_ok = frame.endswith(b"\r")
        if frame_end_ok:
            score += 5
            reasons.append("frame_end_ok")
        else:
            score -= 50
            reasons.append("frame_end_missing")

        body = frame[1:-1] if frame_start_ok and frame_end_ok else frame[1:] if frame_start_ok else b""
        ascii_hex_payload_ok = (
            bool(body)
            and len(body) % 2 == 0
            and _is_upper_hex(body)
        )
        if ascii_hex_payload_ok:
            score += 10
            reasons.append("ascii_hex_payload_ok")
        else:
            score -= 50
            reasons.append("ascii_hex_payload_invalid")

        expected_prefix_ok = frame.startswith(EXPECTED_PREFIX)
        if expected_prefix_ok:
            score += 10
            reasons.append("expected_prefix_ok")
        else:
            score -= 50
            reasons.append("expected_prefix_mismatch")

        not_echo = frame != request.tx
        if not_echo:
            score += 5
            reasons.append("not_echo")
        else:
            score -= 100
            reasons.append("echoed_request")

        plausible_length_ok = MIN_FRAME_BODY_HEX_LEN <= len(body) <= MAX_FRAME_BODY_HEX_LEN
        if plausible_length_ok:
            score += 5
            reasons.append("plausible_length_ok")
        else:
            score -= 30
            reasons.append("implausible_length")

        checksum_ok = False
        checksum_detail = {}
        frame_data = b""
        if frame_start_ok and frame_end_ok and ascii_hex_payload_ok and len(body) >= CHECKSUM_HEX_LEN:
            parts = _checksum_parts(frame)
            if parts is None:
                reasons.append("checksum_not_verified")
            else:
                frame_data, checksum_received = parts
                checksum_calculated = calculate_pylon_checksum(frame_data)
                checksum_detail = {
                    "checksum_received": checksum_received,
                    "checksum_calculated": checksum_calculated,
                }
                if checksum_received == checksum_calculated:
                    checksum_ok = True
                    score += 20
                    reasons.append("checksum_ok")
                else:
                    score -= 100
                    reasons.append("checksum_invalid")
        else:
            reasons.append("checksum_not_verified")

        decoded = self.decode_response(frame, request, checksum_detail)
        sanity_failed = decoded.get("sanity_status") == "failed"
        if sanity_failed:
            score -= 100
            reasons.append("decoded_sanity_failed")

        ok = all(
            [
                frame_start_ok,
                frame_end_ok,
                ascii_hex_payload_ok,
                expected_prefix_ok,
                not_echo,
                plausible_length_ok,
                checksum_ok,
                not sanity_failed,
            ]
        )
        return ValidationResult(ok=ok, score_delta=score, reasons=reasons, decoded=decoded)

    def decode_response(self, frame: bytes, request: ProbeMessage | None = None, checksum_detail: dict | None = None) -> dict:
        decoded = {
            "ascii": frame.decode("ascii", errors="replace").strip(),
            "parse_status": "raw_only",
            "checksum_status": "not_verified",
        }
        if checksum_detail:
            decoded.update(checksum_detail)
            if checksum_detail.get("checksum_received") == checksum_detail.get("checksum_calculated"):
                decoded["checksum_status"] = "verified"
            else:
                decoded["checksum_status"] = "invalid"

        parts = _checksum_parts(frame)
        if parts is None:
            return apply_pylon_sanity(decoded, self.sanity_ranges)
        frame_data, _received = parts
        parsed = _parse_frame_data(frame_data)
        decoded.update(parsed)
        info_hex = parsed.get("info_hex")
        if not isinstance(info_hex, str) or not parsed.get("length_matches_info"):
            return apply_pylon_sanity(decoded, self.sanity_ranges)
        try:
            info = bytes.fromhex(info_hex)
        except ValueError:
            return apply_pylon_sanity(decoded, self.sanity_ranges)
        if request is not None:
            decoded.update(_decode_info(request, info))
        return apply_pylon_sanity(decoded, self.sanity_ranges)
