from pathlib import Path

import main_cli
from core.models import ProbeMessage
from protocols import get_all_profiles, get_profiles, get_research_profiles
from protocols.modbus_rtu import append_crc, build_modbus_read_request, verify_crc
from protocols.pace_rs485_modbus_v1_3 import (
    ALLOWED_FUNCTION_CODES,
    BASIC_BLOCK_CONFIRMED_RX_HEX,
    BASIC_BLOCK_PROBE_NAME,
    BASIC_BLOCK_TX_HEX,
    BULK_CORE_EXCEPTION_RX_HEX,
    BULK_CORE_PROBE_NAME,
    BULK_CORE_TX_HEX,
    CELL8_PROBE_NAME,
    CELL8_CONFIRMED_RX_HEX,
    CELL8_SEMANTIC_WARNING,
    CELL8_TX_HEX,
    CELL16_PROBE_NAME,
    CELL16_CONFIRMED_RX_HEX,
    CELL16_TX_HEX,
    CONFIRMED_RX_HEX,
    FORBIDDEN_FUNCTION_CODES,
    PaceRs485ModbusV13Profile,
    SOURCE_PROBE_NAME,
    SOURCE_TX_HEX,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DOC = PROJECT_DIR / "docs" / "protocol_research" / "pace_rs485_modbus_v1_3.md"


def _args(argv: list[str]):
    return main_cli.build_parser().parse_args(argv)


def _validation_probe() -> ProbeMessage:
    return PaceRs485ModbusV13Profile().probes[0]


def _probe(name: str) -> ProbeMessage:
    profile = PaceRs485ModbusV13Profile()
    for probe in profile.probes:
        if probe.name == name:
            return probe
    raise AssertionError(f"missing probe: {name}")


def _synthetic_bulk_response() -> bytes:
    registers = [0] * 0x31
    registers[0x0000] = 0xFB2E  # -1234 signed, -12.34 A at 10mA units.
    registers[0x0001] = 2629
    registers[0x0002] = 87
    for index, value in enumerate([3288, 3290, 3285, 3289]):
        registers[0x0015 + index] = value
    data = b"".join(value.to_bytes(2, byteorder="big") for value in registers)
    return append_crc(bytes([0x01, 0x03, len(data)]) + data)


def _synthetic_basic_response() -> bytes:
    registers = [
        0xFE0C,  # -500 signed, -5.00 A at 10mA units.
        2629,
        87,
    ]
    data = b"".join(value.to_bytes(2, byteorder="big") for value in registers)
    return append_crc(bytes([0x01, 0x03, len(data)]) + data)


def _synthetic_cell_response(quantity: int) -> bytes:
    values = [3288, 3290, 3285, 3289, 0, 0, 0, 0]
    if quantity == 16:
        values += [3291, 3292, 3287, 3286, 0, 0, 0, 0]
    assert len(values) == quantity
    data = b"".join(value.to_bytes(2, byteorder="big") for value in values)
    return append_crc(bytes([0x01, 0x03, len(data)]) + data)


def test_profile_id_and_metadata_are_active_source_confirmed():
    profile = PaceRs485ModbusV13Profile()

    assert profile.id == "pace_rs485_modbus_v1_3"
    assert profile.name == "PACE RS485 Modbus V1.3"
    assert profile.family == "pace"
    assert profile.transport == "rs485"
    assert profile.protocol_class == "modbus_rtu"
    assert profile.default_baud_candidates == [9600]
    assert profile.serial_format == "8N1"
    assert profile.risk_policy == "safe_read_only"
    assert profile.decode == "minimal_confirmed_decode"
    assert profile.hardware_status == "hardware_confirmed_basic_block_cell_frames_untrusted"
    assert profile.hardware_confirmed is True
    assert profile.source_status == "source_confirmed_pdf"
    assert profile.status == "active_safe_read_basic_block_hardware_confirmed_cell_frames_untrusted"
    assert profile.confirmed_probe == SOURCE_PROBE_NAME
    assert profile.confirmed_tx_hex == SOURCE_TX_HEX
    assert profile.confirmed_rx_hex == CONFIRMED_RX_HEX
    assert profile.confirmed_serial == "9600 8N1"
    assert profile.confirmed_bms_menu == "004 PACE_RS485_Modbus_V1.3"
    assert profile.bulk_core_block_hardware_confirmed is False
    assert profile.bulk_core_block_hardware_result == "modbus_exception_code_02"
    assert profile.bulk_core_block_exception_rx_hex == BULK_CORE_EXCEPTION_RX_HEX
    assert profile.chunked_probe_names == (
        BASIC_BLOCK_PROBE_NAME,
        CELL8_PROBE_NAME,
        CELL16_PROBE_NAME,
    )
    assert profile.basic_block_hardware_confirmed is True
    assert profile.basic_block_semantic_decode_confirmed is True
    assert profile.basic_block_confirmed_rx_hex == BASIC_BLOCK_CONFIRMED_RX_HEX
    assert profile.cell8_hardware_confirmed is True
    assert profile.cell8_modbus_frame_confirmed is True
    assert profile.cell8_semantic_decode_confirmed is False
    assert profile.cell8_decode_status == "frame_valid_semantics_untrusted"
    assert profile.cell8_warning == CELL8_SEMANTIC_WARNING
    assert profile.cell8_confirmed_rx_hex == CELL8_CONFIRMED_RX_HEX
    assert profile.cell16_hardware_confirmed is True
    assert profile.cell16_modbus_frame_confirmed is True
    assert profile.cell16_semantic_decode_confirmed is False
    assert profile.cell16_hardware_result == "confirmed_frame_with_decode_warnings"
    assert profile.cell16_decode_status == "frame_valid_semantics_untrusted"
    assert profile.cell16_warnings == (
        "non_trailing_zero_cell_voltage",
        "cell_voltage_out_of_expected_range",
    )
    assert profile.cell16_confirmed_rx_hex == CELL16_CONFIRMED_RX_HEX
    assert profile.enabled_by_default is True
    assert len(profile.probes) == 5
    assert profile.primary_probe_names == (SOURCE_PROBE_NAME,)


def test_profile_is_separate_from_existing_protocols():
    profile = PaceRs485ModbusV13Profile()
    active_ids = {active.id for active in get_all_profiles()}

    assert profile.id in active_ids
    assert profile.id != "pylon_lv_rs485"
    assert profile.id != "jk_rs485_modbus"
    assert profile.id != "jk_pylon_lv_emulation"
    assert profile.id != "pace_rs485_modbus_rtu"


def test_profile_is_in_active_registry_and_not_research_registry():
    active_ids = {profile.id for profile in get_profiles(include_unverified=False)}
    all_ids = {profile.id for profile in get_profiles(include_unverified=True)}
    research_ids = {profile.id for profile in get_research_profiles()}

    assert "pace_rs485_modbus_v1_3" in active_ids
    assert "pace_rs485_modbus_v1_3" not in research_ids
    assert "pace_rs485_modbus_v1_3" in all_ids


def test_cli_list_profiles_shows_active_pace_profile(capsys, tmp_path):
    code = main_cli.run_cli(
        _args(["--list-profiles"]),
        transport_factory=lambda: None,
        list_ports_func=lambda: [],
        log_dir=tmp_path,
    )
    default_out = capsys.readouterr().out

    assert code == 0
    assert "pace_rs485_modbus_v1_3" in default_out
    assert "enabled=True" in default_out


def test_source_probe_metadata_and_request_crc():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(SOURCE_PROBE_NAME)
    body = bytes.fromhex("01 03 00 01 00 01")

    assert probe.name == SOURCE_PROBE_NAME
    assert probe.tx == bytes.fromhex(SOURCE_TX_HEX)
    assert body + bytes.fromhex("D5 CA") == probe.tx
    assert build_modbus_read_request(1, 0x03, 0x0001, 1) == probe.tx
    assert probe.slave_id == 1
    assert probe.function_code == 0x03
    assert probe.start_register == 0x0001
    assert probe.quantity == 1
    assert probe.risk == "safe_read"
    assert probe.primary is True
    assert probe.hardware_confirmed is True
    assert verify_crc(probe.tx)


def test_bulk_core_probe_metadata_and_request_crc():
    probe = _probe(BULK_CORE_PROBE_NAME)
    body = bytes.fromhex("01 03 00 00 00 31")

    assert probe.name == BULK_CORE_PROBE_NAME
    assert probe.tx == bytes.fromhex(BULK_CORE_TX_HEX)
    assert body + bytes.fromhex("84 1E") == probe.tx
    assert build_modbus_read_request(1, 0x03, 0x0000, 0x0031) == probe.tx
    assert probe.slave_id == 1
    assert probe.function_code == 0x03
    assert probe.start_register == 0x0000
    assert probe.quantity == 0x0031
    assert probe.risk == "safe_read"
    assert probe.primary is False
    assert probe.hardware_confirmed is False
    assert verify_crc(probe.tx)


def test_chunked_probe_metadata_and_request_crc():
    cases = [
        (BASIC_BLOCK_PROBE_NAME, BASIC_BLOCK_TX_HEX, "01 03 00 00 00 03", "05 CB", 0x0000, 3),
        (CELL8_PROBE_NAME, CELL8_TX_HEX, "01 03 00 15 00 08", "55 C8", 0x0015, 8),
        (CELL16_PROBE_NAME, CELL16_TX_HEX, "01 03 00 15 00 10", "55 C2", 0x0015, 16),
    ]

    for name, tx_hex, body_hex, crc_hex, start_register, quantity in cases:
        probe = _probe(name)
        body = bytes.fromhex(body_hex)

        assert probe.name == name
        assert probe.tx == bytes.fromhex(tx_hex)
        assert body + bytes.fromhex(crc_hex) == probe.tx
        assert build_modbus_read_request(1, 0x03, start_register, quantity) == probe.tx
        assert probe.slave_id == 1
        assert probe.function_code == 0x03
        assert probe.start_register == start_register
        assert probe.quantity == quantity
        assert probe.risk == "safe_read"
        assert probe.primary is False
        assert probe.hardware_confirmed is True
        assert verify_crc(probe.tx)
        assert getattr(probe, "modbus_frame_confirmed") is True
        if name == BASIC_BLOCK_PROBE_NAME:
            assert getattr(probe, "semantic_decode_confirmed") is True
        else:
            assert getattr(probe, "semantic_decode_confirmed") is False
            assert getattr(probe, "decode_status") == "frame_valid_semantics_untrusted"


def test_no_write_control_or_forbidden_function_probes_exist():
    profile = PaceRs485ModbusV13Profile()
    blocked_tokens = (
        "write",
        "control",
        "factory",
        "unlock",
        "calibrate",
        "calibration",
        "reset",
        "firmware_update",
        "parameter_set",
        "mos_control",
        "function_0x05",
        "function_0x06",
        "function_0x0f",
        "function_0x10",
    )

    assert FORBIDDEN_FUNCTION_CODES == (0x05, 0x06, 0x0F, 0x10)
    for probe in profile.probes:
        assert probe.risk == "safe_read"
        assert probe.function_code in ALLOWED_FUNCTION_CODES
        assert probe.function_code not in FORBIDDEN_FUNCTION_CODES
        assert not any(token in probe.name.lower() for token in blocked_tokens)


def test_validator_accepts_valid_modbus_read_shape_and_decodes_pack_voltage():
    profile = PaceRs485ModbusV13Profile()
    probe = _validation_probe()
    response = bytes.fromhex(CONFIRMED_RX_HEX)

    result = profile.validate_response(probe, response)

    assert response == bytes.fromhex("01 03 02 0A 45 7F 17")
    assert result.ok
    assert "not_echo" in result.reasons
    assert "crc_ok" in result.reasons
    assert "slave_id_ok" in result.reasons
    assert "function_code_ok" in result.reasons
    assert "byte_count_ok" in result.reasons
    assert "decoded_pack_voltage_ok" in result.reasons
    assert result.decoded["parse_status"] == "decoded"
    assert result.decoded["decode_status"] == "hardware_confirmed_pack_voltage"
    assert result.decoded["crc_status"] == "verified"
    assert result.decoded["register_0x0001_raw"] == 2629
    assert result.decoded["pack_voltage_v"] == 26.29


def test_validator_accepts_bulk_core_block_and_decodes_known_fields():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(BULK_CORE_PROBE_NAME)
    response = _synthetic_bulk_response()

    result = profile.validate_response(probe, response)

    assert len(response) == 103
    assert response[2] == 0x62
    assert result.ok
    assert "not_echo" in result.reasons
    assert "crc_ok" in result.reasons
    assert "slave_id_ok" in result.reasons
    assert "function_code_ok" in result.reasons
    assert "byte_count_ok" in result.reasons
    assert "decoded_bulk_core_block_ok" in result.reasons
    assert result.decoded["decode_status"] == "hardware_bulk_core_block"
    assert result.decoded["registers_raw"]["0x0000"] == 0xFB2E
    assert result.decoded["registers_raw"]["0x0001"] == 2629
    assert result.decoded["registers_raw"]["0x0002"] == 87
    assert result.decoded["current_raw_signed"] == -1234
    assert result.decoded["current_a"] == -12.34
    assert result.decoded["pack_voltage_v"] == 26.29
    assert result.decoded["soc_percent_raw"] == 87
    assert result.decoded["soc_percent"] == 87
    assert result.decoded["cell_voltage_decode_status"] == "frame_valid_semantics_untrusted"
    assert result.decoded["cell_voltage_semantic_decode_confirmed"] is False
    assert result.decoded["raw_candidate_cell_voltages_mv"][:4] == [3288, 3290, 3285, 3289]
    assert result.decoded["raw_candidate_cell_voltages_mv"][4:] == [0] * 24
    assert "active_cell_count" not in result.decoded
    assert "min_cell_mv" not in result.decoded
    assert "max_cell_mv" not in result.decoded
    assert "delta_cell_mv" not in result.decoded
    assert result.decoded["decode_warnings"] == [CELL8_SEMANTIC_WARNING]
    assert len(result.decoded["unused_cell_registers_possible"]) == 24
    assert result.decoded["raw_registers_note"]


def test_validator_accepts_basic_block_and_decodes_known_fields():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(BASIC_BLOCK_PROBE_NAME)
    response = _synthetic_basic_response()

    result = profile.validate_response(probe, response)

    assert len(response) == 11
    assert response[2] == 0x06
    assert result.ok
    assert "byte_count_ok" in result.reasons
    assert "decoded_basic_block_ok" in result.reasons
    assert result.decoded["decode_status"] == "hardware_basic_block"
    assert result.decoded["registers_raw"]["0x0000"] == 0xFE0C
    assert result.decoded["current_raw_signed"] == -500
    assert result.decoded["current_a"] == -5.0
    assert result.decoded["pack_voltage_raw"] == 2629
    assert result.decoded["pack_voltage_v"] == 26.29
    assert result.decoded["soc_percent_raw"] == 87
    assert result.decoded["soc_percent"] == 87


def test_validator_accepts_hardware_basic_block_response():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(BASIC_BLOCK_PROBE_NAME)
    response = bytes.fromhex(BASIC_BLOCK_CONFIRMED_RX_HEX)

    result = profile.validate_response(probe, response)

    assert result.ok
    assert verify_crc(response)
    assert result.decoded["current_a"] == 0.0
    assert result.decoded["pack_voltage_v"] == 26.29
    assert result.decoded["soc_percent"] == 66


def test_validator_accepts_cell8_block_and_decodes_cell_voltages():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(CELL8_PROBE_NAME)
    response = _synthetic_cell_response(8)

    result = profile.validate_response(probe, response)

    assert len(response) == 21
    assert response[2] == 0x10
    assert result.ok
    assert "byte_count_ok" in result.reasons
    assert "cell_voltage_frame_valid_semantics_untrusted" in result.reasons
    assert result.decoded["decode_status"] == "frame_valid_semantics_untrusted"
    assert result.decoded["modbus_frame_confirmed"] is True
    assert result.decoded["semantic_decode_confirmed"] is False
    assert result.decoded["raw_candidate_cell_01_mv"] == 3288
    assert result.decoded["raw_candidate_cell_08_mv"] == 0
    assert result.decoded["raw_candidate_cell_voltages_mv"] == [3288, 3290, 3285, 3289, 0, 0, 0, 0]
    assert "cell_voltages_mv" not in result.decoded
    assert "active_cell_count" not in result.decoded
    assert "min_cell_mv" not in result.decoded
    assert "max_cell_mv" not in result.decoded
    assert "delta_cell_mv" not in result.decoded
    assert len(result.decoded["unused_cell_registers_possible"]) == 4
    assert result.decoded["decode_warnings"] == [CELL8_SEMANTIC_WARNING]


def test_validator_accepts_hardware_cell8_response():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(CELL8_PROBE_NAME)
    response = bytes.fromhex(CELL8_CONFIRMED_RX_HEX)

    result = profile.validate_response(probe, response)

    assert result.ok
    assert verify_crc(response)
    assert result.decoded["decode_status"] == "frame_valid_semantics_untrusted"
    assert result.decoded["modbus_frame_confirmed"] is True
    assert result.decoded["semantic_decode_confirmed"] is False
    assert result.decoded["raw_candidate_cell_voltages_mv"] == [3288, 3287, 0, 0, 0, 0, 0, 0]
    assert result.decoded["decode_warnings"] == [CELL8_SEMANTIC_WARNING]
    assert "cell_voltages_mv" not in result.decoded
    assert "active_cell_count" not in result.decoded
    assert "min_cell_mv" not in result.decoded
    assert "max_cell_mv" not in result.decoded
    assert "delta_cell_mv" not in result.decoded


def test_validator_accepts_cell16_block_and_decodes_cell_voltages():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(CELL16_PROBE_NAME)
    response = _synthetic_cell_response(16)

    result = profile.validate_response(probe, response)

    assert len(response) == 37
    assert response[2] == 0x20
    assert result.ok
    assert "byte_count_ok" in result.reasons
    assert "cell_voltage_frame_valid_semantics_untrusted" in result.reasons
    assert result.decoded["decode_status"] == "frame_valid_semantics_untrusted"
    assert result.decoded["modbus_frame_confirmed"] is True
    assert result.decoded["semantic_decode_confirmed"] is False
    assert result.decoded["raw_candidate_cell_01_mv"] == 3288
    assert result.decoded["raw_candidate_cell_16_mv"] == 0
    assert result.decoded["raw_candidate_cell_voltages_mv"] == [
        3288,
        3290,
        3285,
        3289,
        0,
        0,
        0,
        0,
        3291,
        3292,
        3287,
        3286,
        0,
        0,
        0,
        0,
    ]
    assert "cell_voltages_mv" not in result.decoded
    assert "active_cell_count" not in result.decoded
    assert "min_cell_mv" not in result.decoded
    assert "max_cell_mv" not in result.decoded
    assert "delta_cell_mv" not in result.decoded
    assert len(result.decoded["unused_cell_registers_possible"]) == 8
    assert result.decoded["decode_warnings"] == ["non_trailing_zero_cell_voltage"]


def test_validator_accepts_hardware_cell16_response_with_warnings():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(CELL16_PROBE_NAME)
    response = bytes.fromhex(CELL16_CONFIRMED_RX_HEX)

    result = profile.validate_response(probe, response)

    assert result.ok
    assert verify_crc(response)
    assert result.decoded["decode_status"] == "frame_valid_semantics_untrusted"
    assert result.decoded["modbus_frame_confirmed"] is True
    assert result.decoded["semantic_decode_confirmed"] is False
    assert result.decoded["raw_candidate_cell_voltages_mv"] == [
        3287,
        3285,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        210,
        209,
        63536,
        63536,
        241,
        209,
    ]
    assert result.decoded["decode_warnings"] == [
        "non_trailing_zero_cell_voltage",
        "cell_voltage_out_of_expected_range",
    ]
    assert "cell_voltages_mv" not in result.decoded
    assert "active_cell_count" not in result.decoded
    assert "min_cell_mv" not in result.decoded
    assert "max_cell_mv" not in result.decoded
    assert "delta_cell_mv" not in result.decoded


def test_wrong_crc_rejected():
    profile = PaceRs485ModbusV13Profile()
    probe = _validation_probe()
    corrupted = bytearray(append_crc(bytes.fromhex("01 03 02 12 34")))
    corrupted[-1] ^= 0xFF

    result = profile.validate_response(probe, bytes(corrupted))

    assert not result.ok
    assert "crc_invalid" in result.reasons


def test_wrong_slave_rejected():
    profile = PaceRs485ModbusV13Profile()
    probe = _validation_probe()
    response = append_crc(bytes.fromhex("02 03 02 12 34"))

    result = profile.validate_response(probe, response)

    assert not result.ok
    assert "slave_id_mismatch" in result.reasons


def test_wrong_function_rejected():
    profile = PaceRs485ModbusV13Profile()
    probe = _validation_probe()
    response = append_crc(bytes.fromhex("01 04 02 12 34"))

    result = profile.validate_response(probe, response)

    assert not result.ok
    assert "function_code_mismatch" in result.reasons


def test_wrong_byte_count_rejected():
    profile = PaceRs485ModbusV13Profile()
    probe = _validation_probe()
    response = append_crc(bytes.fromhex("01 03 04 12 34"))

    result = profile.validate_response(probe, response)

    assert not result.ok
    assert "byte_count_mismatch" in result.reasons


def test_modbus_exception_response_is_negative_match():
    profile = PaceRs485ModbusV13Profile()
    probe = _validation_probe()
    response = append_crc(bytes.fromhex("01 83 02"))

    result = profile.validate_response(probe, response)

    assert not result.ok
    assert "modbus_exception_response" in result.reasons
    assert "exception_code_02" in result.reasons
    assert result.decoded["crc_status"] == "verified"


def test_bulk_core_hardware_exception_response_is_negative_match():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(BULK_CORE_PROBE_NAME)
    response = bytes.fromhex(BULK_CORE_EXCEPTION_RX_HEX)

    result = profile.validate_response(probe, response)

    assert verify_crc(response)
    assert not result.ok
    assert "not_echo" in result.reasons
    assert "crc_ok" in result.reasons
    assert "slave_id_ok" in result.reasons
    assert "modbus_exception_response" in result.reasons
    assert "exception_code_02" in result.reasons
    assert result.decoded["parse_status"] == "raw_only"
    assert result.decoded["crc_status"] == "verified"


def test_echo_rejected():
    profile = PaceRs485ModbusV13Profile()
    probe = _validation_probe()

    result = profile.validate_response(probe, probe.tx)

    assert not result.ok
    assert "echoed_request" in result.reasons


def test_bulk_wrong_byte_count_rejected():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(BULK_CORE_PROBE_NAME)
    response = bytearray(_synthetic_bulk_response())
    response[2] = 0x60
    response = append_crc(bytes(response[:-2]))

    result = profile.validate_response(probe, response)

    assert not result.ok
    assert "byte_count_mismatch" in result.reasons


def test_bulk_echo_rejected():
    profile = PaceRs485ModbusV13Profile()
    probe = _probe(BULK_CORE_PROBE_NAME)

    result = profile.validate_response(probe, probe.tx)

    assert not result.ok
    assert "echoed_request" in result.reasons


def test_chunked_exception_response_is_negative_match():
    profile = PaceRs485ModbusV13Profile()
    for probe_name in (BASIC_BLOCK_PROBE_NAME, CELL8_PROBE_NAME, CELL16_PROBE_NAME):
        probe = _probe(probe_name)
        response = append_crc(bytes.fromhex("01 83 02"))

        result = profile.validate_response(probe, response)

        assert not result.ok
        assert "modbus_exception_response" in result.reasons
        assert "exception_code_02" in result.reasons
        assert result.decoded["parse_status"] == "raw_only"


def test_chunked_wrong_byte_count_rejected():
    profile = PaceRs485ModbusV13Profile()
    cases = [
        (BASIC_BLOCK_PROBE_NAME, append_crc(bytes.fromhex("01 03 04 00 01 00 02"))),
        (CELL8_PROBE_NAME, append_crc(bytes.fromhex("01 03 0E") + b"\x00" * 14)),
        (CELL16_PROBE_NAME, append_crc(bytes.fromhex("01 03 1E") + b"\x00" * 30)),
    ]

    for probe_name, response in cases:
        result = profile.validate_response(_probe(probe_name), response)

        assert not result.ok
        assert "byte_count_mismatch" in result.reasons


def test_chunked_echo_rejected():
    profile = PaceRs485ModbusV13Profile()
    for probe_name in (BASIC_BLOCK_PROBE_NAME, CELL8_PROBE_NAME, CELL16_PROBE_NAME):
        probe = _probe(probe_name)

        result = profile.validate_response(probe, probe.tx)

        assert not result.ok
        assert "echoed_request" in result.reasons


def test_research_doc_contains_required_boundaries():
    text = RESEARCH_DOC.read_text(encoding="utf-8")

    assert "# PACE RS485 Modbus V1.3" in text
    assert (
        "active safe-read / hardware-confirmed basic block / cell voltage frames confirmed but semantic decode untrusted"
        in text
    )
    assert "PACE basic current/voltage/SOC works on the tested BMS." in text
    assert "PACE cell-voltage register interpretation is not trusted yet." in text
    assert "cross-checked against JK native Modbus or the BMS app" in text
    assert "004 PACE_RS485_Modbus_V1.3" in text
    assert "PACE BMS Modbus Protocol for RS485 V1.3 (2017-06-27)" in text
    assert "Register `0001`: Voltage of pack, R/UINT16, unit 10mV." in text
    assert "read_pack_voltage_addr1" in text
    assert "01 03 00 01 00 01 D5 CA" in text
    assert "read_core_block_0_48_addr1" in text
    assert "01 03 00 00 00 31 84 1E" in text
    assert "read_basic_block_0_2_addr1" in text
    assert "01 03 00 00 00 03 05 CB" in text
    assert "01 03 06 00 00 0A 45 00 42 B3 49" in text
    assert "read_cell_voltages_0_7_addr1" in text
    assert "01 03 00 15 00 08 55 C8" in text
    assert "01 03 10 0C D8 0C D7 00 00 00 00 00 00 00 00 00 00 00 00 01 DC" in text
    assert "raw_candidate_cell_voltages_mv: `[3288, 3287, 0, 0, 0, 0, 0, 0]`" in text
    assert "read_cell_voltages_0_15_addr1" in text
    assert "01 03 00 15 00 10 55 C2" in text
    assert "01 03 20 0C D7 0C D5 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 D2 00 D1 F8 30 F8 30 00 F1 00 D1 64 1A" in text
    assert "frame_valid_semantics_untrusted" in text
    assert "semantic_decode_confirmed: false" in text
    assert "raw_candidate_cell_voltages_mv: `[3287, 3285, 0, 0, 0, 0, 0, 0, 0, 0, 210, 209, 63536, 63536, 241, 209]`" in text
    assert "01 83 02 C0 F1" in text
    assert "modbus_exception_response" in text
    assert "exception_code_02" in text
    assert "01 03 02 0A 45 7F 17" in text
    assert "Decoded pack voltage: 26.29 V" in text
    assert "hardware_confirmed_single_probe" in text
    assert "Do not confuse with Pylon low voltage RS485 ASCII." in text
    assert "Do not confuse with PACE paceic ASCII protocol." in text
    assert "<slave> <function> <byte_count> <data...> <crc_lo> <crc_hi>" in text
    assert "FC05, FC06, FC0F, or FC10" in text
    assert verify_crc(build_modbus_read_request(1, 0x03, 0x0001, 1))
