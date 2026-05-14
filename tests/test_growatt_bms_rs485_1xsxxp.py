from pathlib import Path

import main_cli
from protocols import get_all_profiles, get_profiles, get_research_profiles
from protocols.growatt_bms_rs485_1xsxxp import (
    ALLOWED_FUNCTION_CODES,
    CELL8_PROBE_NAME,
    CELL8_CONFIRMED_RX_HEX,
    CELL8_TX_HEX,
    CELL16_PROBE_NAME,
    CELL16_CONFIRMED_RX_HEX,
    CELL16_TX_HEX,
    CONFIRMED_RX_HEX,
    FORBIDDEN_FUNCTION_CODES,
    PROBE_NAME,
    PROFILE_ID,
    SOURCE_REFERENCE,
    SOURCE_SERIAL,
    SOURCE_TX_HEX,
    STATUS_BLOCK_PROBE_NAME,
    STATUS_BLOCK_CONFIRMED_RX_HEX,
    STATUS_BLOCK_TX_HEX,
    GrowattBmsRs4851xSxxpProfile,
)
from protocols.modbus_rtu import append_crc, build_modbus_read_request, verify_crc

PROJECT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DOC = PROJECT_DIR / "docs" / "protocol_research" / "growatt_bms_rs485_1xsxxp.md"


def _args(argv: list[str]):
    return main_cli.build_parser().parse_args(argv)


def _probe():
    return GrowattBmsRs4851xSxxpProfile().probes[0]


def _probe_by_name(name: str):
    return next(probe for probe in GrowattBmsRs4851xSxxpProfile().probes if probe.name == name)


def _valid_response_for_probe(probe):
    if probe.name == PROBE_NAME:
        return bytes.fromhex(CONFIRMED_RX_HEX)
    if probe.name == STATUS_BLOCK_PROBE_NAME:
        return append_crc(bytes.fromhex("01 03 0C 00 01 00 00 00 42 0A 45 00 00 00 19"))
    if probe.name == CELL8_PROBE_NAME:
        values = [3288, 3287, 3289, 3288, 3287, 3288, 3289, 3288]
    elif probe.name == CELL16_PROBE_NAME:
        values = [3288, 3287, 3289, 3288, 3287, 3288, 3289, 3288] + [0] * 8
    else:
        raise AssertionError(f"unexpected probe {probe.name}")
    payload = b"".join(value.to_bytes(2, byteorder="big") for value in values)
    return append_crc(bytes([1, 3, len(payload)]) + payload)


def test_profile_metadata_is_active_source_confirmed_hardware_confirmed():
    profile = GrowattBmsRs4851xSxxpProfile()

    assert profile.id == PROFILE_ID
    assert profile.name == "Growatt BMS RS485 1xSxxP ESS safe-read"
    assert profile.family == "growatt"
    assert profile.transport == "rs485"
    assert profile.protocol_class == "modbus_rtu"
    assert profile.default_baud_candidates == [9600]
    assert profile.serial_format == "8N1"
    assert profile.risk_policy == "safe_read_only"
    assert profile.decode == "minimal_confirmed_soc"
    assert profile.hardware_status == "hardware_confirmed_status_block_cell_frames_semantics_suspicious"
    assert profile.hardware_confirmed is True
    assert profile.source_status == "source_confirmed_pdf"
    assert profile.source_reference == SOURCE_REFERENCE
    assert profile.source_serial == SOURCE_SERIAL
    assert profile.status == "active_safe_read_status_block_hardware_confirmed_cell_frames_suspicious"
    assert profile.confirmed_probe == PROBE_NAME
    assert profile.confirmed_tx_hex == SOURCE_TX_HEX
    assert profile.confirmed_rx_hex == CONFIRMED_RX_HEX
    assert profile.confirmed_serial == "9600 8N1"
    assert profile.confirmed_bms_menu == "006 Growatt_BMS_RS485_Protocol_1x..."
    assert profile.source_confirmed_probe == PROBE_NAME
    assert profile.source_confirmed_tx_hex == SOURCE_TX_HEX
    assert profile.source_confirmed_block_probes == (
        STATUS_BLOCK_PROBE_NAME,
        CELL8_PROBE_NAME,
        CELL16_PROBE_NAME,
    )
    assert profile.status_block_hardware_confirmed is True
    assert profile.status_block_confirmed_rx_hex == STATUS_BLOCK_CONFIRMED_RX_HEX
    assert profile.cell8_hardware_confirmed is True
    assert profile.cell8_modbus_frame_confirmed is True
    assert profile.cell8_semantic_decode_confirmed is False
    assert profile.cell8_decode_status == "frame_valid_semantics_suspicious"
    assert profile.cell8_confirmed_rx_hex == CELL8_CONFIRMED_RX_HEX
    assert profile.cell16_hardware_confirmed is True
    assert profile.cell16_modbus_frame_confirmed is True
    assert profile.cell16_semantic_decode_confirmed is False
    assert profile.cell16_decode_status == "frame_valid_semantics_suspicious"
    assert profile.cell16_confirmed_rx_hex == CELL16_CONFIRMED_RX_HEX
    assert profile.enabled_by_default is True
    assert profile.primary_probe_names == (PROBE_NAME,)
    assert len(profile.probes) == 4


def test_profile_is_active_and_separate_from_existing_protocols():
    profile = GrowattBmsRs4851xSxxpProfile()
    active_ids = {active.id for active in get_all_profiles()}
    all_ids = {active.id for active in get_profiles(include_unverified=True)}
    research_ids = {active.id for active in get_research_profiles()}

    assert PROFILE_ID in active_ids
    assert PROFILE_ID in all_ids
    assert PROFILE_ID not in research_ids
    assert profile.id != "pylon_lv_rs485"
    assert profile.id != "pace_rs485_modbus_v1_3"
    assert profile.id != "jk_rs485_modbus"
    assert profile.id != "growatt_ess_rs485_candidate"


def test_cli_list_profiles_shows_active_growatt_profile(capsys, tmp_path):
    code = main_cli.run_cli(
        _args(["--list-profiles"]),
        transport_factory=lambda: None,
        list_ports_func=lambda: [],
        log_dir=tmp_path,
    )
    default_out = capsys.readouterr().out

    assert code == 0
    assert PROFILE_ID in default_out
    assert "enabled=True" in default_out


def test_source_probe_metadata_and_request_crc():
    probe = _probe()
    body = bytes.fromhex("01 03 00 15 00 01")

    assert probe.name == PROBE_NAME
    assert probe.tx == bytes.fromhex(SOURCE_TX_HEX)
    assert body + bytes.fromhex("95 CE") == probe.tx
    assert build_modbus_read_request(1, 0x03, 0x0015, 1) == probe.tx
    assert probe.slave_id == 1
    assert probe.function_code == 0x03
    assert probe.start_register == 0x0015
    assert probe.quantity == 1
    assert probe.risk == "safe_read"
    assert probe.primary is True
    assert probe.hardware_confirmed is True
    assert verify_crc(probe.tx)


def test_source_confirmed_block_probe_metadata_and_request_crc():
    expected = {
        STATUS_BLOCK_PROBE_NAME: (0x0013, 6, STATUS_BLOCK_TX_HEX),
        CELL8_PROBE_NAME: (0x0071, 8, CELL8_TX_HEX),
        CELL16_PROBE_NAME: (0x0071, 16, CELL16_TX_HEX),
    }

    for name, (start_register, quantity, tx_hex) in expected.items():
        probe = _probe_by_name(name)

        assert probe.tx == bytes.fromhex(tx_hex)
        assert probe.tx == build_modbus_read_request(1, 0x03, start_register, quantity)
        assert probe.slave_id == 1
        assert probe.function_code == 0x03
        assert probe.start_register == start_register
        assert probe.quantity == quantity
        assert probe.risk == "safe_read"
        assert probe.primary is False
        assert probe.hardware_confirmed is True
        assert getattr(probe, "source_confirmed") is True
        assert getattr(probe, "modbus_frame_confirmed") is True
        if name in {CELL8_PROBE_NAME, CELL16_PROBE_NAME}:
            assert getattr(probe, "semantic_decode_confirmed") is False
        else:
            assert getattr(probe, "semantic_decode_confirmed") is True
        assert getattr(probe, "expected_byte_count") == quantity * 2
        assert verify_crc(probe.tx)


def test_no_write_control_or_forbidden_function_probes_exist():
    profile = GrowattBmsRs4851xSxxpProfile()
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

    assert ALLOWED_FUNCTION_CODES == (0x03,)
    assert FORBIDDEN_FUNCTION_CODES == (0x05, 0x06, 0x0F, 0x10)
    for probe in profile.probes:
        assert probe.risk == "safe_read"
        assert probe.function_code in ALLOWED_FUNCTION_CODES
        assert probe.function_code not in FORBIDDEN_FUNCTION_CODES
        assert not any(token in probe.name.lower() for token in blocked_tokens)


def test_validator_accepts_valid_confirmed_response_and_decodes_soc():
    profile = GrowattBmsRs4851xSxxpProfile()
    probe = _probe()
    response = bytes.fromhex(CONFIRMED_RX_HEX)

    result = profile.validate_response(probe, response)

    assert result.ok
    assert verify_crc(response)
    assert "not_echo" in result.reasons
    assert "crc_ok" in result.reasons
    assert "slave_id_ok" in result.reasons
    assert "function_code_ok" in result.reasons
    assert "byte_count_ok" in result.reasons
    assert "decoded_soc_ok" in result.reasons
    assert result.decoded["parse_status"] == "decoded"
    assert result.decoded["decode_status"] == "hardware_confirmed_single_register"
    assert result.decoded["crc_status"] == "verified"
    assert result.decoded["slave_id"] == 1
    assert result.decoded["function_code"] == 3
    assert result.decoded["byte_count"] == 2
    assert result.decoded["register_0x0015_raw"] == 66
    assert result.decoded["soc_raw"] == 66
    assert result.decoded["soc_percent_raw"] == 66
    assert result.decoded["soc_percent"] == 66


def test_validator_accepts_source_status_block_and_decodes_known_fields():
    profile = GrowattBmsRs4851xSxxpProfile()
    probe = _probe_by_name(STATUS_BLOCK_PROBE_NAME)
    response = _valid_response_for_probe(probe)

    result = profile.validate_response(probe, response)

    assert result.ok
    assert "not_echo" in result.reasons
    assert "crc_ok" in result.reasons
    assert "slave_id_ok" in result.reasons
    assert "function_code_ok" in result.reasons
    assert "byte_count_ok" in result.reasons
    assert "decoded_status_block_ok" in result.reasons
    assert result.decoded["decode_status"] == "hardware_confirmed_status_block"
    assert result.decoded["registers_raw"]["0x0013"] == 1
    assert result.decoded["registers_raw"]["0x0015"] == 66
    assert result.decoded["soc_raw"] == 66
    assert result.decoded["soc_percent"] == 66
    assert result.decoded["pack_voltage_raw"] == 2629
    assert result.decoded["pack_voltage_v"] == 26.29
    assert result.decoded["current_raw_signed"] == 0
    assert result.decoded["current_a"] == 0.0
    assert result.decoded["temperature_c"] == 25


def test_validator_accepts_source_cell8_block_and_decodes_cell_voltages():
    profile = GrowattBmsRs4851xSxxpProfile()
    probe = _probe_by_name(CELL8_PROBE_NAME)
    response = _valid_response_for_probe(probe)

    result = profile.validate_response(probe, response)

    assert result.ok
    assert "byte_count_ok" in result.reasons
    assert "cell_voltage_frame_valid_semantics_suspicious" in result.reasons
    assert result.decoded["decode_status"] == "frame_valid_semantics_suspicious"
    assert result.decoded["semantic_decode_confirmed"] is False
    assert result.decoded["modbus_frame_confirmed"] is True
    assert result.decoded["raw_candidate_cell_voltages_mv"] == [
        3288,
        3287,
        3289,
        3288,
        3287,
        3288,
        3289,
        3288,
    ]
    assert result.decoded["raw_candidate_active_cell_count"] == 8
    assert "cell_voltages_mv" not in result.decoded
    assert "active_cell_count" not in result.decoded
    assert "cell_voltage_min_mv" not in result.decoded
    assert "cell_voltage_max_mv" not in result.decoded
    assert "cell_voltage_delta_mv" not in result.decoded


def test_validator_accepts_source_cell16_block_and_marks_trailing_zeros_unused():
    profile = GrowattBmsRs4851xSxxpProfile()
    probe = _probe_by_name(CELL16_PROBE_NAME)
    response = _valid_response_for_probe(probe)

    result = profile.validate_response(probe, response)

    assert result.ok
    assert "cell_voltage_frame_valid_semantics_suspicious" in result.reasons
    assert result.decoded["decode_status"] == "frame_valid_semantics_suspicious"
    assert result.decoded["semantic_decode_confirmed"] is False
    assert result.decoded["raw_candidate_cell_voltages_mv"] == [
        3288,
        3287,
        3289,
        3288,
        3287,
        3288,
        3289,
        3288,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    assert result.decoded["raw_candidate_active_cell_count"] == 8
    assert len(result.decoded["unused_cell_registers_possible"]) == 8
    assert "cell_voltages_mv" not in result.decoded
    assert "active_cell_count" not in result.decoded
    assert "cell_voltage_min_mv" not in result.decoded
    assert "cell_voltage_max_mv" not in result.decoded
    assert "cell_voltage_delta_mv" not in result.decoded
    assert "decode_warnings" not in result.decoded


def test_validator_accepts_hardware_status_block_response():
    profile = GrowattBmsRs4851xSxxpProfile()
    probe = _probe_by_name(STATUS_BLOCK_PROBE_NAME)
    result = profile.validate_response(probe, bytes.fromhex(STATUS_BLOCK_CONFIRMED_RX_HEX))

    assert result.ok
    assert "decoded_status_block_ok" in result.reasons
    assert result.decoded["decode_status"] == "hardware_confirmed_status_block"
    assert result.decoded["registers_raw"] == {
        "0x0013": 1129,
        "0x0014": 0,
        "0x0015": 66,
        "0x0016": 2631,
        "0x0017": 0,
        "0x0018": 20,
    }
    assert result.decoded["soc_percent"] == 66
    assert result.decoded["pack_voltage_v"] == 26.31
    assert result.decoded["current_a"] == 0.0
    assert result.decoded["temperature_c"] == 20


def test_validator_accepts_hardware_cell8_response():
    profile = GrowattBmsRs4851xSxxpProfile()
    probe = _probe_by_name(CELL8_PROBE_NAME)
    result = profile.validate_response(probe, bytes.fromhex(CELL8_CONFIRMED_RX_HEX))

    assert result.ok
    assert "cell_voltage_frame_valid_semantics_suspicious" in result.reasons
    assert result.decoded["decode_status"] == "frame_valid_semantics_suspicious"
    assert result.decoded["semantic_decode_confirmed"] is False
    assert result.decoded["raw_candidate_cell_voltages_mv"] == [3289, 3289, 3290, 3290, 3289, 3290, 3290, 0]
    assert result.decoded["raw_candidate_active_cell_voltages_mv"] == [
        3289,
        3289,
        3290,
        3290,
        3289,
        3290,
        3290,
    ]
    assert result.decoded["raw_candidate_active_cell_count"] == 7
    assert result.decoded["raw_candidate_cell_sum_v"] == 23.027
    assert result.decoded["reference_pack_voltage_v"] == 26.31
    assert result.decoded["expected_cell_count_from_pack_voltage"] == 8
    assert "cell_sum_mismatch_pack_voltage" in result.decoded["decode_warnings"]
    assert "active_cell_count_mismatch_pack_voltage" in result.decoded["decode_warnings"]
    assert "cell_voltages_mv" not in result.decoded
    assert "active_cell_count" not in result.decoded
    assert "cell_voltage_min_mv" not in result.decoded
    assert "cell_voltage_max_mv" not in result.decoded
    assert "cell_voltage_delta_mv" not in result.decoded
    assert result.decoded["unused_cell_registers_possible"] == [
        {"cell": 8, "register": "0x0078", "status": "unused_possible"}
    ]


def test_validator_accepts_hardware_cell16_response():
    profile = GrowattBmsRs4851xSxxpProfile()
    probe = _probe_by_name(CELL16_PROBE_NAME)
    result = profile.validate_response(probe, bytes.fromhex(CELL16_CONFIRMED_RX_HEX))

    assert result.ok
    assert "cell_voltage_frame_valid_semantics_suspicious" in result.reasons
    assert result.decoded["decode_status"] == "frame_valid_semantics_suspicious"
    assert result.decoded["semantic_decode_confirmed"] is False
    assert result.decoded["raw_candidate_cell_voltages_mv"] == [
        3289,
        3290,
        3290,
        3289,
        3289,
        3290,
        3290,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    assert result.decoded["raw_candidate_active_cell_voltages_mv"] == [
        3289,
        3290,
        3290,
        3289,
        3289,
        3290,
        3290,
    ]
    assert result.decoded["raw_candidate_active_cell_count"] == 7
    assert result.decoded["raw_candidate_cell_sum_v"] == 23.027
    assert result.decoded["reference_pack_voltage_v"] == 26.31
    assert result.decoded["expected_cell_count_from_pack_voltage"] == 8
    assert "cell_sum_mismatch_pack_voltage" in result.decoded["decode_warnings"]
    assert "active_cell_count_mismatch_pack_voltage" in result.decoded["decode_warnings"]
    assert "cell_voltages_mv" not in result.decoded
    assert "active_cell_count" not in result.decoded
    assert "cell_voltage_min_mv" not in result.decoded
    assert "cell_voltage_max_mv" not in result.decoded
    assert "cell_voltage_delta_mv" not in result.decoded
    assert len(result.decoded["unused_cell_registers_possible"]) == 9


def test_wrong_crc_rejected_for_all_growatt_probes():
    profile = GrowattBmsRs4851xSxxpProfile()
    for probe in profile.probes:
        corrupted = bytearray(_valid_response_for_probe(probe))
        corrupted[-1] ^= 0xFF

        result = profile.validate_response(probe, bytes(corrupted))

        assert not result.ok
        assert "crc_invalid" in result.reasons


def test_echo_rejected_for_all_growatt_probes():
    profile = GrowattBmsRs4851xSxxpProfile()
    for probe in profile.probes:
        result = profile.validate_response(probe, probe.tx)

        assert not result.ok
        assert "echoed_request" in result.reasons


def test_wrong_slave_rejected_for_all_growatt_probes():
    profile = GrowattBmsRs4851xSxxpProfile()
    for probe in profile.probes:
        response = bytearray(_valid_response_for_probe(probe))
        response[0] = 2
        response = append_crc(bytes(response[:-2]))

        result = profile.validate_response(probe, response)

        assert not result.ok
        assert "slave_id_mismatch" in result.reasons


def test_wrong_function_rejected_for_all_growatt_probes():
    profile = GrowattBmsRs4851xSxxpProfile()
    for probe in profile.probes:
        response = bytearray(_valid_response_for_probe(probe))
        response[1] = 4
        response = append_crc(bytes(response[:-2]))

        result = profile.validate_response(probe, response)

        assert not result.ok
        assert "function_code_mismatch" in result.reasons


def test_wrong_byte_count_rejected_for_all_growatt_probes():
    profile = GrowattBmsRs4851xSxxpProfile()
    for probe in profile.probes:
        response = bytearray(_valid_response_for_probe(probe))
        response[2] += 2
        response = append_crc(bytes(response[:-2]))

        result = profile.validate_response(probe, response)

        assert not result.ok
        assert "byte_count_mismatch" in result.reasons


def test_modbus_exception_response_is_negative_match_for_all_growatt_probes():
    profile = GrowattBmsRs4851xSxxpProfile()
    for probe in profile.probes:
        response = append_crc(bytes.fromhex("01 83 02"))

        result = profile.validate_response(probe, response)

        assert not result.ok
        assert "modbus_exception_response" in result.reasons
        assert "exception_code_02" in result.reasons
        assert result.decoded["crc_status"] == "verified"


def test_research_doc_contains_boundaries_and_source_terms():
    text = RESEARCH_DOC.read_text(encoding="utf-8")

    assert "# Growatt BMS RS485 1xSxxP ESS" in text
    assert "cell-voltage Modbus" in text
    assert "frames confirmed but semantic decode suspicious" in text
    assert "006 Growatt_BMS_RS485_Protocol_1x" in text
    assert SOURCE_REFERENCE in text
    assert "Modbus RTU" in text
    assert "9600 8N1" in text
    assert "FC03" in text
    assert "0x0015" in text
    assert "01 03 00 15 00 01 95 CE" in text
    assert "Do not confuse with Growatt Inverter Modbus RTU Protocol." in text
    assert "Do not confuse with Growatt BMS CAN protocol." in text
    assert "No FC05, FC06, FC0F, or FC10 probes." in text
    assert "hardware-confirmed single read-only probe" in text
    assert "Decoded SOC: `66 %`" in text
    assert "single_probe_growatt_bms_rs485_1xsxxp_read_soc_addr1_20260514T061543Z.json" in text
    assert "hardware_confirmed_single_register" in text
    assert "JSON decoded SOC percent: `66`" in text
    assert "frame_valid_semantics_suspicious" in text
    assert "semantic_decode_confirmed: `false`" in text
    assert "raw_candidate_cell_voltages_mv" in text
    assert "cell_sum_mismatch_pack_voltage" in text
    assert "active_cell_count_mismatch_pack_voltage" in text
    assert "possible off-by-one register-map mismatch" in text
