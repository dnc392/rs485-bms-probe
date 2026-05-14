from pathlib import Path

import main_cli
import json
from protocols import get_all_profiles, get_profiles, get_research_profiles
from transport.fake_serial_transport import FakeSerialTransport
from protocols.modbus_rtu import append_crc, build_modbus_read_request, verify_crc
from protocols.voltronic_inverter_bms_485 import (
    ALLOWED_FUNCTION_CODES,
    FORBIDDEN_FUNCTION_CODES,
    PROBE_NAME,
    OBSERVED_RX_HEX,
    PROFILE_ID,
    SOURCE_REFERENCE,
    SOURCE_SERIAL,
    SOURCE_TX_HEX,
    SOURCE_URL,
    VoltronicInverterBms485Profile,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DOC = PROJECT_DIR / "docs" / "protocol_research" / "voltronic_inverter_bms_485.md"


def _args(argv: list[str]):
    return main_cli.build_parser().parse_args(argv)


def _probe():
    return VoltronicInverterBms485Profile().probes[0]


def _valid_response() -> bytes:
    return bytes.fromhex(OBSERVED_RX_HEX)


def test_profile_metadata_is_active_source_custom_hardware_confirmed():
    profile = VoltronicInverterBms485Profile()

    assert profile.id == PROFILE_ID
    assert profile.name == "Voltronic Inverter and BMS 485 safe-read"
    assert profile.family == "voltronic"
    assert profile.transport == "rs485"
    assert profile.protocol_class == "modbus_rtu_like"
    assert profile.default_baud_candidates == [9600]
    assert profile.serial_format == "8N1"
    assert profile.risk_policy == "safe_read_only"
    assert profile.decode == "minimal_confirmed_cell_count_source_custom"
    assert profile.hardware_status == "hardware_confirmed_source_custom_single_probe"
    assert profile.hardware_confirmed is True
    assert profile.standard_modbus_confirmed is False
    assert profile.source_custom_response_confirmed is True
    assert profile.source_status == "source_confirmed_docx"
    assert profile.source_reference == SOURCE_REFERENCE
    assert profile.source_url == SOURCE_URL
    assert profile.source_serial == SOURCE_SERIAL
    assert profile.status == "active_safe_read_single_probe_hardware_confirmed_source_custom"
    assert profile.source_confirmed_probe == PROBE_NAME
    assert profile.source_confirmed_tx_hex == SOURCE_TX_HEX
    assert profile.confirmed_probe == PROBE_NAME
    assert profile.confirmed_tx_hex == SOURCE_TX_HEX
    assert profile.confirmed_rx_hex == OBSERVED_RX_HEX
    assert profile.confirmed_serial == "9600 8N1"
    assert profile.confirmed_bms_menu == "007 Voltronic_Inverter_and_BMS_485-..."
    assert profile.enabled_by_default is True
    assert profile.primary_probe_names == (PROBE_NAME,)
    assert len(profile.probes) == 1


def test_profile_is_active_and_separate_from_existing_protocols():
    profile = VoltronicInverterBms485Profile()
    active_ids = {active.id for active in get_all_profiles()}
    all_ids = {active.id for active in get_profiles(include_unverified=True)}
    research_ids = {active.id for active in get_research_profiles()}

    assert PROFILE_ID in active_ids
    assert PROFILE_ID in all_ids
    assert PROFILE_ID not in research_ids
    assert profile.id != "pylon_lv_rs485"
    assert profile.id != "growatt_bms_rs485_1xsxxp"
    assert profile.id != "pace_rs485_modbus_v1_3"
    assert profile.id != "jk_rs485_modbus"


def test_cli_list_profiles_shows_active_voltronic_profile(capsys, tmp_path):
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
    body = bytes.fromhex("01 03 00 10 00 01")

    assert probe.name == PROBE_NAME
    assert probe.tx == bytes.fromhex(SOURCE_TX_HEX)
    assert body + bytes.fromhex("85 CF") == probe.tx
    assert build_modbus_read_request(1, 0x03, 0x0010, 1) == probe.tx
    assert probe.slave_id == 1
    assert probe.function_code == 0x03
    assert probe.start_register == 0x0010
    assert probe.quantity == 1
    assert probe.risk == "safe_read"
    assert probe.primary is True
    assert probe.hardware_confirmed is True
    assert getattr(probe, "source_confirmed") is True
    assert getattr(probe, "expected_byte_count") == 2
    assert getattr(probe, "standard_modbus_confirmed") is False
    assert getattr(probe, "source_custom_response_confirmed") is True
    assert getattr(probe, "confirmed_tx_hex") == SOURCE_TX_HEX
    assert getattr(probe, "confirmed_rx_hex") == OBSERVED_RX_HEX
    assert verify_crc(probe.tx)


def test_no_write_control_or_forbidden_function_probes_exist():
    profile = VoltronicInverterBms485Profile()
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


def test_validator_accepts_source_custom_response_shape_and_decodes_cell_count():
    profile = VoltronicInverterBms485Profile()
    response = _valid_response()

    result = profile.validate_response(_probe(), response)

    assert response == bytes.fromhex("01 03 00 01 00 08 15 CC")
    assert result.ok
    assert "not_echo" in result.reasons
    assert "crc_ok" in result.reasons
    assert "slave_id_ok" in result.reasons
    assert "function_code_ok" in result.reasons
    assert "voltronic_custom_data_length_ok" in result.reasons
    assert "source_response_length_ok" in result.reasons
    assert "source_custom_response_confirmed" in result.reasons
    assert "standard_modbus_request_shape_ambiguous" in result.reasons
    assert result.decoded["parse_status"] == "decoded"
    assert result.decoded["protocol_shape"] == "voltronic_source_custom_response"
    assert result.decoded["crc_status"] == "verified"
    assert result.decoded["slave_id"] == 1
    assert result.decoded["function_code"] == 3
    assert result.decoded["command_type"] == 3
    assert result.decoded["byte_count"] is None
    assert result.decoded["source_data_length_words"] == 1
    assert result.decoded["source_data_hex"] == "00 08"
    assert result.decoded["classification"] == "source_custom_response_confirmed"
    assert result.decoded["data_length_words"] == 1
    assert result.decoded["data_bytes"] == "00 08"
    assert result.decoded["register_0x0010_raw"] == 8
    assert result.decoded["cell_count"] == 8
    assert result.decoded["decode_status"] == "hardware_confirmed_single_register_source_custom"
    assert result.decoded["warnings"] == [
        "standard_modbus_request_shape_ambiguous",
        "not_standard_modbus_response",
    ]


def test_wrong_crc_rejected():
    profile = VoltronicInverterBms485Profile()
    response = bytearray(_valid_response())
    response[-1] ^= 0xFF

    result = profile.validate_response(_probe(), bytes(response))

    assert not result.ok
    assert "crc_invalid" in result.reasons


def test_echo_rejected():
    profile = VoltronicInverterBms485Profile()

    result = profile.validate_response(_probe(), _probe().tx)

    assert not result.ok
    assert "echoed_request" in result.reasons


def test_wrong_slave_rejected():
    profile = VoltronicInverterBms485Profile()
    response = append_crc(bytes.fromhex("02 03 00 01 00 08"))

    result = profile.validate_response(_probe(), response)

    assert not result.ok
    assert "slave_id_mismatch" in result.reasons


def test_wrong_function_rejected():
    profile = VoltronicInverterBms485Profile()
    response = append_crc(bytes.fromhex("01 04 00 01 00 08"))

    result = profile.validate_response(_probe(), response)

    assert not result.ok
    assert "function_code_mismatch" in result.reasons


def test_wrong_source_data_length_rejected():
    profile = VoltronicInverterBms485Profile()
    response = append_crc(bytes.fromhex("01 03 00 02 00 08"))

    result = profile.validate_response(_probe(), response)

    assert not result.ok
    assert "data_length_mismatch" in result.reasons
    assert "byte_count_mismatch" in result.reasons
    assert result.decoded["classification"] == "valid_crc_unexpected_modbus_request_shape"


def test_extra_payload_byte_rejected():
    profile = VoltronicInverterBms485Profile()
    response = append_crc(bytes.fromhex("01 03 00 01 00 08 00"))

    result = profile.validate_response(_probe(), response)

    assert not result.ok
    assert "response_length_mismatch" in result.reasons


def test_abnormal_response_is_negative_match():
    profile = VoltronicInverterBms485Profile()
    abnormal_response = append_crc(bytes.fromhex("01 83 02"))

    result = profile.validate_response(_probe(), abnormal_response)

    assert abnormal_response == bytes.fromhex("01 83 02 C0 F1")
    assert not result.ok
    assert "modbus_exception_response" in result.reasons
    assert "voltronic_abnormal_response" in result.reasons
    assert "error_code_02" in result.reasons
    assert "exception_code_02" in result.reasons
    assert result.decoded["crc_status"] == "verified"


def test_hardware_attempt_source_custom_shape_is_hardware_confirmed_source_custom():
    profile = VoltronicInverterBms485Profile()
    hardware_rx = bytes.fromhex("01 03 00 01 00 08 15 CC")

    result = profile.validate_response(_probe(), hardware_rx)

    assert verify_crc(hardware_rx)
    assert result.ok
    assert profile.hardware_confirmed is True
    assert profile.standard_modbus_confirmed is False
    assert profile.source_custom_response_confirmed is True
    assert "not_echo" in result.reasons
    assert "crc_ok" in result.reasons
    assert "slave_id_ok" in result.reasons
    assert "function_code_ok" in result.reasons
    assert "voltronic_custom_data_length_ok" in result.reasons
    assert "source_response_length_ok" in result.reasons
    assert "standard_modbus_request_shape_ambiguous" in result.reasons
    assert result.decoded["parse_status"] == "decoded"
    assert result.decoded["crc_status"] == "verified"
    assert result.decoded["classification"] == "source_custom_response_confirmed"
    assert result.decoded["source_data_length_words"] == 1
    assert result.decoded["source_data_hex"] == "00 08"
    assert result.decoded["protocol_shape"] == "voltronic_source_custom_response"
    assert result.decoded["register_0x0010_raw"] == 8
    assert result.decoded["cell_count"] == 8
    assert result.decoded["warnings"] == [
        "standard_modbus_request_shape_ambiguous",
        "not_standard_modbus_response",
    ]


def test_single_probe_cli_writes_decoded_cell_count_to_json(capsys, tmp_path):
    transport = FakeSerialTransport([bytes.fromhex(OBSERVED_RX_HEX)])

    code = main_cli.run_cli(
        _args(
            [
                "--single-probe",
                "--profile",
                PROFILE_ID,
                "--probe",
                PROBE_NAME,
                "--port",
                "COM3",
                "--baud",
                "9600",
                "--parity",
                "N",
                "--stopbits",
                "1",
            ]
        ),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["COM3"],
        log_dir=tmp_path,
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "Decoded:" in out
    assert "- cell_count: 8" in out
    log_path = next(tmp_path.glob(f"single_probe_{PROFILE_ID}_{PROBE_NAME}_*.json"))
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    entry = payload["entries"][0]
    assert entry["tx_hex"] == SOURCE_TX_HEX
    assert entry["rx_hex"] == OBSERVED_RX_HEX
    assert entry["decoded"]["decode_status"] == "hardware_confirmed_single_register_source_custom"
    assert entry["decoded"]["cell_count"] == 8
    assert entry["decoded"]["warnings"] == [
        "standard_modbus_request_shape_ambiguous",
        "not_standard_modbus_response",
    ]


def test_research_doc_contains_boundaries_and_source_terms():
    text = RESEARCH_DOC.read_text(encoding="utf-8")

    assert "# Voltronic Inverter and BMS 485" in text
    assert "007 Voltronic_Inverter_and_BMS_485" in text
    assert SOURCE_REFERENCE in text
    assert SOURCE_URL in text
    assert "9600 8N1" in text
    assert "0x03" in text
    assert "0x10" in text
    assert "write data and is forbidden" in text
    assert "0x0010" in text
    assert "01 03 00 10 00 01 85 CF" in text
    assert "Do not confuse with the generic Voltronic inverter serial protocol" in text
    assert "No FC05, FC06, FC0F, or FC10 probes." in text
    assert "single_probe_voltronic_inverter_bms_485_read_cell_count_addr1_20260514T072823Z.json" in text
    assert "source-custom single-probe hardware-confirmed" in text
    assert "source_custom_response_confirmed" in text
    assert "standard Modbus request-shaped" in text
    assert "Decoded cell_count: `8`" in text
    assert "not standard Modbus RTU response shape" in text
