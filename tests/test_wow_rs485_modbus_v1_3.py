import json
from pathlib import Path

import pytest

import main_cli
from core.diagnostics import select_safe_probe
from core.scanner import run_active_probe
from protocols import get_all_profiles, get_profiles, get_research_profiles
from protocols.modbus_rtu import append_crc, verify_crc
from protocols.wow_rs485_modbus_v1_3 import (
    EXPERIMENTAL_BLOCK_OBSERVED_RESPONSE_HEX,
    EXPERIMENTAL_BLOCK_PROBE_ID,
    EXPERIMENTAL_BLOCK_REQUEST_HEX,
    EXPERIMENTAL_CELL_OBSERVED_RESPONSE_HEX,
    EXPERIMENTAL_CELL_PROBE_ID,
    EXPERIMENTAL_CELL_REQUEST_HEX,
    EXPERIMENTAL_OBSERVED_RESPONSE_HEX,
    EXPERIMENTAL_PROBE_ID,
    EXPERIMENTAL_REQUEST_HEX,
    FORBIDDEN_FUNCTION_CODES,
    PROFILE_ID,
    SOURCE_MENU,
    WowRs485ModbusV13Profile,
)
from transport.fake_serial_transport import FakeSerialTransport

PROJECT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DOC = PROJECT_DIR / "docs" / "protocol_research" / "wow_rs485_modbus_v1_3.md"


def _args(argv: list[str]):
    return main_cli.build_parser().parse_args(argv)


def _valid_response(raw_value: int = 0x1234) -> bytes:
    return append_crc(bytes([0x01, 0x03, 0x02]) + raw_value.to_bytes(2, byteorder="big"))


def _valid_block_response(current_raw: int = 0, voltage_raw: int = 2630, soc_raw: int = 66) -> bytes:
    data = b"".join(
        value.to_bytes(2, byteorder="big")
        for value in (current_raw & 0xFFFF, voltage_raw & 0xFFFF, soc_raw & 0xFFFF)
    )
    return append_crc(bytes([0x01, 0x03, 0x06]) + data)


def _valid_cell_response(values: list[int] | None = None) -> bytes:
    if values is None:
        values = [3288, 3287, 3288, 3287, 3287, 3288, 3287, 3288]
    data = b"".join(value.to_bytes(2, byteorder="big") for value in values)
    return append_crc(bytes([0x01, 0x03, 0x10]) + data)


def _exception_response(code: int = 0x02) -> bytes:
    return append_crc(bytes([0x01, 0x83, code]))


def _probe(profile: WowRs485ModbusV13Profile, name: str):
    return next(probe for probe in profile.probes if probe.name == name)


def test_profile_metadata_is_inactive_research_with_experimental_probe():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_PROBE_ID)
    block_probe = _probe(profile, EXPERIMENTAL_BLOCK_PROBE_ID)
    cell_probe = _probe(profile, EXPERIMENTAL_CELL_PROBE_ID)

    assert profile.id == PROFILE_ID
    assert profile.name == "WOW RS485 Modbus V1.3 research-only"
    assert profile.family == "wow"
    assert profile.transport == "rs485"
    assert profile.protocol_class == "experimental_standard_modbus_rtu_assumption"
    assert profile.status == "inactive_research_with_experimental_read"
    assert profile.enabled_by_default is False
    assert profile.hardware_status == "unverified_hardware"
    assert profile.hardware_confirmed is False
    assert profile.hardware_observed is True
    assert profile.hardware_confirmed_experimental is True
    assert profile.experimental_observed_tx_hex == EXPERIMENTAL_REQUEST_HEX
    assert profile.experimental_observed_rx_hex == EXPERIMENTAL_OBSERVED_RESPONSE_HEX
    assert profile.experimental_block_observed_tx_hex == EXPERIMENTAL_BLOCK_REQUEST_HEX
    assert profile.experimental_block_observed_rx_hex == EXPERIMENTAL_BLOCK_OBSERVED_RESPONSE_HEX
    assert profile.experimental_cell_observed_tx_hex == EXPERIMENTAL_CELL_REQUEST_HEX
    assert profile.experimental_cell_observed_rx_hex == EXPERIMENTAL_CELL_OBSERVED_RESPONSE_HEX
    assert profile.source_status == "missing_confirmed_safe_read_request"
    assert profile.experimental_probe_count == 3
    assert profile.bms_menu == SOURCE_MENU
    assert profile.reason == "missing_confirmed_safe_read_request"
    assert profile.risk_policy == "explicit_experimental_unverified_read_only"
    assert profile.decode == "raw_only"
    assert profile.primary_probe_names == ()

    assert probe.name == EXPERIMENTAL_PROBE_ID
    assert probe.request_hex == EXPERIMENTAL_REQUEST_HEX
    assert probe.risk == "experimental_unverified_read"
    assert probe.risk != "safe_read"
    assert probe.slave_id == 1
    assert probe.function_code == 0x03
    assert probe.start_register == 0x0001
    assert probe.quantity == 1
    assert probe.hardware_confirmed is False
    assert probe.hardware_observed is True
    assert probe.hardware_confirmed_experimental is True
    assert probe.confirmed_rx_hex == EXPERIMENTAL_OBSERVED_RESPONSE_HEX
    assert probe.source_confirmed is False
    assert probe.enabled_by_default is False
    assert probe.requires_explicit_unverified_flag is True

    assert block_probe.name == EXPERIMENTAL_BLOCK_PROBE_ID
    assert block_probe.request_hex == EXPERIMENTAL_BLOCK_REQUEST_HEX
    assert block_probe.risk == "experimental_unverified_read"
    assert block_probe.risk != "safe_read"
    assert block_probe.slave_id == 1
    assert block_probe.function_code == 0x03
    assert block_probe.start_register == 0x0000
    assert block_probe.quantity == 3
    assert block_probe.hardware_confirmed is False
    assert block_probe.hardware_observed is True
    assert block_probe.hardware_confirmed_experimental is True
    assert block_probe.confirmed_rx_hex == EXPERIMENTAL_BLOCK_OBSERVED_RESPONSE_HEX
    assert block_probe.source_confirmed is False
    assert block_probe.enabled_by_default is False
    assert block_probe.requires_explicit_unverified_flag is True

    assert cell_probe.name == EXPERIMENTAL_CELL_PROBE_ID
    assert cell_probe.request_hex == EXPERIMENTAL_CELL_REQUEST_HEX
    assert cell_probe.risk == "experimental_unverified_read"
    assert cell_probe.risk != "safe_read"
    assert cell_probe.slave_id == 1
    assert cell_probe.function_code == 0x03
    assert cell_probe.start_register == 0x0015
    assert cell_probe.quantity == 8
    assert cell_probe.hardware_confirmed is False
    assert cell_probe.hardware_observed is True
    assert cell_probe.hardware_confirmed_experimental is True
    assert cell_probe.confirmed_rx_hex == EXPERIMENTAL_CELL_OBSERVED_RESPONSE_HEX
    assert cell_probe.frame_valid is True
    assert cell_probe.semantic_confirmed is False
    assert cell_probe.semantic_status == "frame_valid_semantics_failed"
    assert cell_probe.failure_reason == "candidate_cell_sum_mismatch_pack_voltage"
    assert cell_probe.source_confirmed is False
    assert cell_probe.enabled_by_default is False
    assert cell_probe.requires_explicit_unverified_flag is True


def test_profile_is_research_only_and_not_active():
    active_ids = {profile.id for profile in get_all_profiles()}
    all_ids = {profile.id for profile in get_profiles(include_unverified=True)}
    research_ids = {profile.id for profile in get_research_profiles()}

    assert PROFILE_ID not in active_ids
    assert PROFILE_ID in all_ids
    assert PROFILE_ID in research_ids
    assert PROFILE_ID != "pace_rs485_modbus_v1_3"
    assert PROFILE_ID != "growatt_bms_rs485_1xsxxp"
    assert PROFILE_ID != "voltronic_inverter_bms_485"
    assert PROFILE_ID != "jk_rs485_modbus"
    assert PROFILE_ID != "pylon_lv_rs485"


def test_cli_list_profiles_hides_wow_by_default_and_shows_include_unverified(capsys, tmp_path):
    code = main_cli.run_cli(
        _args(["--list-profiles"]),
        transport_factory=lambda: None,
        list_ports_func=lambda: [],
        log_dir=tmp_path,
    )
    default_out = capsys.readouterr().out

    assert code == 0
    assert PROFILE_ID not in default_out

    code = main_cli.run_cli(
        _args(["--list-profiles", "--include-unverified"]),
        transport_factory=lambda: None,
        list_ports_func=lambda: [],
        log_dir=tmp_path,
    )
    include_out = capsys.readouterr().out

    assert code == 0
    assert PROFILE_ID in include_out
    assert "enabled=False" in include_out
    assert "experimental_unverified_read" in include_out


def test_experimental_request_crc():
    request_without_crc = bytes.fromhex("01 03 00 01 00 01")
    request = append_crc(request_without_crc)

    assert request.hex(" ").upper() == EXPERIMENTAL_REQUEST_HEX
    assert verify_crc(request)


def test_experimental_block_request_crc():
    request_without_crc = bytes.fromhex("01 03 00 00 00 03")
    request = append_crc(request_without_crc)

    assert request.hex(" ").upper() == EXPERIMENTAL_BLOCK_REQUEST_HEX
    assert verify_crc(request)


def test_experimental_cell_voltage_request_crc():
    request_without_crc = bytes.fromhex("01 03 00 15 00 08")
    request = append_crc(request_without_crc)

    assert request.hex(" ").upper() == EXPERIMENTAL_CELL_REQUEST_HEX
    assert verify_crc(request)


def test_experimental_probe_requires_explicit_unverified_flag():
    profile = WowRs485ModbusV13Profile()

    with pytest.raises(ValueError, match="unverified probe disabled"):
        select_safe_probe(profile, EXPERIMENTAL_PROBE_ID)

    probe = select_safe_probe(profile, EXPERIMENTAL_PROBE_ID, include_unverified=True)

    assert probe.name == EXPERIMENTAL_PROBE_ID
    assert probe.risk == "experimental_unverified_read"

    with pytest.raises(ValueError, match="unverified probe disabled"):
        select_safe_probe(profile, EXPERIMENTAL_BLOCK_PROBE_ID)

    block_probe = select_safe_probe(profile, EXPERIMENTAL_BLOCK_PROBE_ID, include_unverified=True)
    assert block_probe.name == EXPERIMENTAL_BLOCK_PROBE_ID
    assert block_probe.risk == "experimental_unverified_read"

    with pytest.raises(ValueError, match="unverified probe disabled"):
        select_safe_probe(profile, EXPERIMENTAL_CELL_PROBE_ID)

    cell_probe = select_safe_probe(profile, EXPERIMENTAL_CELL_PROBE_ID, include_unverified=True)
    assert cell_probe.name == EXPERIMENTAL_CELL_PROBE_ID
    assert cell_probe.risk == "experimental_unverified_read"


def test_cli_single_probe_without_include_unverified_does_not_open_transport(tmp_path):
    transport = FakeSerialTransport([_valid_response()])

    with pytest.raises(ValueError, match="Invalid profile id"):
        main_cli.run_cli(
            _args(
                [
                    "--single-probe",
                    "--profile",
                    PROFILE_ID,
                    "--probe",
                    EXPERIMENTAL_PROBE_ID,
                    "--port",
                    "COM3",
                ]
            ),
            transport_factory=lambda: transport,
            list_ports_func=lambda: ["COM3"],
            log_dir=tmp_path,
        )

    assert transport.writes == []
    assert not list(tmp_path.glob("single_probe_wow_rs485_modbus_v1_3_*.json"))


def test_cli_single_probe_with_include_unverified_runs_and_logs_raw_only(capsys, tmp_path):
    transport = FakeSerialTransport([_valid_response()])

    code = main_cli.run_cli(
        _args(
            [
                "--single-probe",
                "--include-unverified",
                "--profile",
                PROFILE_ID,
                "--probe",
                EXPERIMENTAL_PROBE_ID,
                "--port",
                "COM3",
            ]
        ),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["COM3"],
        log_dir=tmp_path,
    )
    out = capsys.readouterr().out
    logs = list(tmp_path.glob("single_probe_wow_rs485_modbus_v1_3_*.json"))
    payload = json.loads(logs[0].read_text(encoding="utf-8"))
    entry = payload["entries"][0]

    assert code == 0
    assert "WARNING:" in out
    assert transport.writes == [bytes.fromhex(EXPERIMENTAL_REQUEST_HEX)]
    assert entry["tx_hex"] == EXPERIMENTAL_REQUEST_HEX
    assert entry["decoded"]["parse_status"] == "raw_only"
    assert entry["decoded"]["classification"] == "experimental_modbus_response_valid"
    assert "experimental_modbus_response_valid" in entry["hardware_status"]


def test_experimental_probe_is_not_used_by_scan_even_with_include_unverified():
    profile = WowRs485ModbusV13Profile()
    transport = FakeSerialTransport([_valid_response()])

    result = run_active_probe(transport, "FAKE0", profile, include_unverified=True)

    assert transport.writes == []
    assert result.detected is False
    assert transport.writes == []
    assert result.detected is False
    assert result.skipped_probes == [
        {
            "probe": EXPERIMENTAL_PROBE_ID,
            "reason": "Blocked by scan policy (experimental probe disabled).",
        },
        {
            "probe": EXPERIMENTAL_BLOCK_PROBE_ID,
            "reason": "Blocked by scan policy (experimental probe disabled).",
        },
        {
            "probe": EXPERIMENTAL_CELL_PROBE_ID,
            "reason": "Blocked by scan policy (experimental probe disabled).",
        },
    ]


def test_no_write_control_or_forbidden_function_probes_exist():
    profile = WowRs485ModbusV13Profile()

    assert len(profile.probes) == 3
    for probe in profile.probes:
        assert probe.risk == "experimental_unverified_read"
        assert probe.function_code not in FORBIDDEN_FUNCTION_CODES
        lower_name = probe.name.lower()
        assert "write" not in lower_name
        assert "control" not in lower_name
        assert "reset" not in lower_name
        assert "factory" not in lower_name


def test_synthetic_valid_response_accepted():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_PROBE_ID)

    result = profile.validate_response(probe, _valid_response())

    assert result.ok is True
    assert result.reasons == ["not_echo", "crc_ok", "slave_id_ok", "function_code_ok", "byte_count_ok"]
    assert result.decoded["parse_status"] == "raw_only"
    assert result.decoded["classification"] == "experimental_modbus_response_valid"


def test_synthetic_block_response_accepted_with_candidate_decode():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_BLOCK_PROBE_ID)

    result = profile.validate_response(probe, _valid_block_response())

    assert result.ok is True
    assert result.reasons == ["not_echo", "crc_ok", "slave_id_ok", "function_code_ok", "byte_count_ok"]
    assert result.decoded["parse_status"] == "raw_only"
    assert result.decoded["classification"] == "experimental_modbus_response_valid"
    assert result.decoded["decode_status"] == "experimental_candidate_decode"
    assert result.decoded["semantic_confirmed"] is False
    assert result.decoded["candidate_register_0x0000_raw"] == 0
    assert result.decoded["candidate_register_0x0001_raw"] == 2630
    assert result.decoded["candidate_register_0x0002_raw"] == 66
    assert result.decoded["candidate_current_a"] == 0.0
    assert result.decoded["candidate_pack_voltage_v"] == 26.3
    assert result.decoded["candidate_soc_percent"] == 66


def test_synthetic_cell_voltage_response_accepted_with_candidate_decode():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_CELL_PROBE_ID)

    result = profile.validate_response(probe, _valid_cell_response())

    assert result.ok is True
    assert result.reasons == ["not_echo", "crc_ok", "slave_id_ok", "function_code_ok", "byte_count_ok"]
    assert result.decoded["parse_status"] == "raw_only"
    assert result.decoded["classification"] == "experimental_modbus_response_valid"
    assert result.decoded["decode_status"] == "experimental_candidate_decode"
    assert result.decoded["semantic_confirmed"] is False
    assert result.decoded["candidate_cell_voltages_mv"] == [3288, 3287, 3288, 3287, 3287, 3288, 3287, 3288]
    assert result.decoded["candidate_active_cell_voltages_mv"] == [3288, 3287, 3288, 3287, 3287, 3288, 3287, 3288]
    assert result.decoded["candidate_active_cell_count"] == 8
    assert result.decoded["candidate_min_cell_mv"] == 3287
    assert result.decoded["candidate_max_cell_mv"] == 3288
    assert result.decoded["candidate_delta_cell_mv"] == 1
    assert result.decoded["candidate_cell_sum_v"] == 26.3
    assert result.decoded["candidate_info"] == ["candidate_cell_sum_matches_pack_voltage"]


def test_actual_hardware_observed_block_response_accepted_as_experimental_only():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_BLOCK_PROBE_ID)

    result = profile.validate_response(probe, bytes.fromhex(EXPERIMENTAL_BLOCK_OBSERVED_RESPONSE_HEX))

    assert result.ok is True
    assert result.reasons == ["not_echo", "crc_ok", "slave_id_ok", "function_code_ok", "byte_count_ok"]
    assert result.decoded["parse_status"] == "raw_only"
    assert result.decoded["classification"] == "experimental_modbus_response_valid"
    assert result.decoded["decode_status"] == "experimental_candidate_decode"
    assert result.decoded["semantic_confirmed"] is False
    assert result.decoded["candidate_register_0x0000_raw"] == 0
    assert result.decoded["candidate_register_0x0001_raw"] == 2630
    assert result.decoded["candidate_register_0x0002_raw"] == 66
    assert result.decoded["candidate_current_a"] == 0.0
    assert result.decoded["candidate_pack_voltage_v"] == 26.3
    assert result.decoded["candidate_soc_percent"] == 66
    assert probe.source_confirmed is False
    assert probe.risk == "experimental_unverified_read"
    assert probe.hardware_confirmed is False
    assert probe.hardware_confirmed_experimental is True


def test_actual_hardware_observed_cell_response_accepted_as_experimental_only():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_CELL_PROBE_ID)

    result = profile.validate_response(probe, bytes.fromhex(EXPERIMENTAL_CELL_OBSERVED_RESPONSE_HEX))

    assert result.ok is True
    assert result.reasons == ["not_echo", "crc_ok", "slave_id_ok", "function_code_ok", "byte_count_ok"]
    assert result.decoded["parse_status"] == "raw_only"
    assert result.decoded["classification"] == "experimental_modbus_response_valid"
    assert result.decoded["frame_valid"] is True
    assert result.decoded["decode_status"] == "experimental_candidate_decode"
    assert result.decoded["semantic_confirmed"] is False
    assert result.decoded["semantic_status"] == "frame_valid_semantics_failed"
    assert result.decoded["candidate_cell_voltages_mv"] == [3289, 3287, 0, 0, 0, 0, 0, 0]
    assert result.decoded["candidate_active_cell_voltages_mv"] == [3289, 3287]
    assert result.decoded["candidate_active_cell_count"] == 2
    assert result.decoded["candidate_min_cell_mv"] == 3287
    assert result.decoded["candidate_max_cell_mv"] == 3289
    assert result.decoded["candidate_delta_cell_mv"] == 2
    assert result.decoded["candidate_cell_sum_v"] == 6.576
    assert result.decoded["candidate_warnings"] == ["candidate_cell_sum_mismatch_pack_voltage"]
    assert result.decoded["failure_reason"] == "candidate_cell_sum_mismatch_pack_voltage"
    assert probe.source_confirmed is False
    assert probe.risk == "experimental_unverified_read"
    assert probe.hardware_confirmed is False
    assert probe.hardware_confirmed_experimental is True


def test_actual_hardware_observed_response_accepted_as_experimental_only():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_PROBE_ID)

    result = profile.validate_response(probe, bytes.fromhex(EXPERIMENTAL_OBSERVED_RESPONSE_HEX))

    assert result.ok is True
    assert result.reasons == ["not_echo", "crc_ok", "slave_id_ok", "function_code_ok", "byte_count_ok"]
    assert result.decoded["parse_status"] == "raw_only"
    assert result.decoded["classification"] == "experimental_modbus_response_valid"
    assert result.decoded["candidate_register_0x0001_raw"] == 2630
    assert probe.source_confirmed is False
    assert probe.risk == "experimental_unverified_read"
    assert probe.hardware_confirmed is False
    assert probe.hardware_confirmed_experimental is True


def test_wrong_crc_rejected():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_CELL_PROBE_ID)
    response = bytearray(_valid_cell_response())
    response[-1] ^= 0xFF

    result = profile.validate_response(probe, bytes(response))

    assert result.ok is False
    assert "crc_invalid" in result.reasons
    assert result.decoded["classification"] == "experimental_invalid_crc"


def test_echo_rejected():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_CELL_PROBE_ID)

    result = profile.validate_response(probe, probe.tx)

    assert result.ok is False
    assert "echoed_request" in result.reasons
    assert result.decoded["classification"] == "experimental_unexpected_shape"


def test_exception_response_handled_as_negative():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_CELL_PROBE_ID)

    result = profile.validate_response(probe, _exception_response(0x02))

    assert result.ok is False
    assert "modbus_exception_response" in result.reasons
    assert "exception_code_02" in result.reasons
    assert result.decoded["classification"] == "experimental_modbus_exception"


def test_request_shaped_or_custom_frame_is_unexpected_shape():
    profile = WowRs485ModbusV13Profile()
    probe = _probe(profile, EXPERIMENTAL_PROBE_ID)
    request_shaped = bytes.fromhex("01 03 00 01 00 08 15 CC")

    result = profile.validate_response(probe, request_shaped)

    assert result.ok is False
    assert "experimental_unexpected_shape" in result.reasons
    assert "byte_count_mismatch" in result.reasons
    assert result.decoded["classification"] == "experimental_unexpected_shape"


def test_research_doc_records_experimental_boundaries():
    text = RESEARCH_DOC.read_text(encoding="utf-8")

    assert "# WOW RS485 Modbus V1.3" in text
    assert "009 WOW_RS485_Modbus_V1.3" in text
    assert "inactive_research_with_experimental_read" in text
    assert "missing_confirmed_safe_read_request" in text
    assert "experimental_read_reg_0x0001_qty1_addr1" in text
    assert "experimental_read_basic_block_0x0000_0x0002_addr1" in text
    assert "experimental_read_cell_voltages_0_7_addr1" in text
    assert "experimental_unverified_read" in text
    assert "This does not make WOW source-confirmed." in text
    assert "This does not make WOW active by default." in text
    assert "No FC05, FC06, FC0F, FC10." in text
    assert "Do not reuse PACE RS485 Modbus V1.3 register map" in text
