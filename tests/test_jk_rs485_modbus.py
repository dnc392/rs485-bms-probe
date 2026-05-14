import json

import main_cli
from core.diagnostics import select_safe_probe
from core.scanner import run_active_probe
from protocols import get_all_profiles
from protocols.jk_rs485_modbus import (
    ALLOWED_FUNCTION_CODES,
    CONFIRMED_CELL_BLOCK_0_7_RX_HEX,
    CONFIRMED_CELL_BLOCK_0_7_TX_HEX,
    CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME,
    CONFIRMED_CELL_BLOCK_0_15_RX_HEX,
    CONFIRMED_CELL_BLOCK_0_15_TX_HEX,
    CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME,
    CONFIRMED_FIRST_READ,
    CONFIRMED_PROBE_ALIAS,
    CONFIRMED_PROBE_NAME,
    CONFIRMED_RX_HEX,
    CONFIRMED_TX_HEX,
    FORBIDDEN_FUNCTION_CODES,
    JkRs485ModbusProfile,
)
from protocols.modbus_rtu import append_crc, build_modbus_read_request, crc16_modbus, verify_crc
from transport.fake_serial_transport import FakeSerialTransport


CONFIRMED_TX = bytes.fromhex(CONFIRMED_TX_HEX)
CONFIRMED_RX = bytes.fromhex(CONFIRMED_RX_HEX)
CONFIRMED_TX_QTY8 = bytes.fromhex(CONFIRMED_CELL_BLOCK_0_7_TX_HEX)
CONFIRMED_RX_QTY8 = bytes.fromhex(CONFIRMED_CELL_BLOCK_0_7_RX_HEX)
CONFIRMED_TX_QTY16 = bytes.fromhex(CONFIRMED_CELL_BLOCK_0_15_TX_HEX)
CONFIRMED_RX_QTY16 = bytes.fromhex(CONFIRMED_CELL_BLOCK_0_15_RX_HEX)


def _args(argv: list[str]):
    return main_cli.build_parser().parse_args(argv)


def _cell_voltage_response(values: list[int]) -> bytes:
    payload = b"".join(value.to_bytes(2, byteorder="big") for value in values)
    return append_crc(bytes([1, 3, len(payload)]) + payload)


def test_jk_rs485_modbus_profile_exists_and_is_active_safe_read():
    profile = JkRs485ModbusProfile()
    active_ids = [profile.id for profile in get_all_profiles()]

    assert profile.id == "jk_rs485_modbus"
    assert profile.enabled_by_default is True
    assert profile.id in active_ids
    assert profile.status == "active_safe_read_hardware_confirmed_cell_voltage_probes"
    assert profile.hardware_confirmed is True
    assert profile.confirmed_probe == CONFIRMED_PROBE_NAME
    assert profile.confirmed_probes == (
        CONFIRMED_PROBE_NAME,
        CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME,
        CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME,
    )
    assert profile.confirmed_tx_hex == CONFIRMED_TX_HEX
    assert profile.confirmed_rx_hex == CONFIRMED_RX_HEX
    assert profile.confirmed_probe_captures[CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME]["rx_hex"]
    assert profile.confirmed_probe_captures[CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME]["rx_hex"]


def test_active_registry_contains_jk_modbus_as_distinct_profile():
    assert [profile.id for profile in get_all_profiles()] == [
        "pylon_lv_rs485",
        "jk_pylon_lv_emulation",
        "jbd_xiaoxiang_uart_rs485",
        "daly_uart_485",
        "jk_rs485_modbus",
        "pace_rs485_modbus_v1_3",
        "growatt_bms_rs485_1xsxxp",
        "voltronic_inverter_bms_485",
    ]


def test_confirmed_probe_metadata_includes_active_cell_voltage_reads():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]
    probes = {probe.name: probe for probe in profile.probes}

    assert len(profile.probes) == 3
    assert CONFIRMED_FIRST_READ.hardware_confirmed is True
    assert probe.name == CONFIRMED_PROBE_NAME
    assert probe.slave_id == 1
    assert probe.function_code == 0x03
    assert probe.start_register == 0x1200
    assert probe.quantity == 1
    assert probe.request_hex == CONFIRMED_TX_HEX
    assert probe.risk == "safe_read"
    assert probe.primary is True
    assert probe.hardware_confirmed is True
    assert CONFIRMED_PROBE_ALIAS in probe.aliases
    assert probes[CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME].quantity == 8
    assert probes[CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME].primary is True
    assert probes[CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME].hardware_confirmed is True
    assert probes[CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME].request_hex == CONFIRMED_CELL_BLOCK_0_7_TX_HEX
    assert probes[CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME].quantity == 16
    assert probes[CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME].primary is False
    assert probes[CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME].hardware_confirmed is True
    assert probes[CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME].request_hex == CONFIRMED_CELL_BLOCK_0_15_TX_HEX
    assert profile.primary_probe_names == (CONFIRMED_PROBE_NAME, CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME)


def test_jk_rs485_modbus_profile_has_only_read_probes():
    profile = JkRs485ModbusProfile()

    assert profile.probes
    assert ALLOWED_FUNCTION_CODES == (0x03, 0x04)
    assert FORBIDDEN_FUNCTION_CODES == (0x05, 0x06, 0x0F, 0x10)
    for probe in profile.probes:
        assert probe.risk == "safe_read"
        assert probe.function_code in ALLOWED_FUNCTION_CODES
        assert probe.function_code not in FORBIDDEN_FUNCTION_CODES
        assert probe.tx[1] in ALLOWED_FUNCTION_CODES
        assert probe.tx[1] not in FORBIDDEN_FUNCTION_CODES
        assert verify_crc(probe.tx)
        assert "write" not in probe.name.lower()
        assert "control" not in probe.name.lower()


def test_jk_rs485_modbus_request_crc_for_confirmed_probe():
    body = bytes.fromhex("01 03 12 00 00 01")
    request = build_modbus_read_request(1, 0x03, 0x1200, 1)

    assert crc16_modbus(body).to_bytes(2, byteorder="little") == bytes.fromhex("81 72")
    assert request == CONFIRMED_TX
    assert verify_crc(request)
    assert build_modbus_read_request(1, 0x03, 0x1200, 8) == CONFIRMED_TX_QTY8
    assert build_modbus_read_request(1, 0x03, 0x1200, 16) == CONFIRMED_TX_QTY16


def test_jk_rs485_modbus_hardware_response_crc_valid():
    assert append_crc(bytes.fromhex("01 03 02 0C D8")) == CONFIRMED_RX
    assert verify_crc(CONFIRMED_RX)
    assert verify_crc(CONFIRMED_RX_QTY8)
    assert verify_crc(CONFIRMED_RX_QTY16)


def test_jk_rs485_modbus_confirmed_response_is_accepted_and_decoded():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]

    result = profile.validate_response(probe, CONFIRMED_RX)

    assert result.ok
    assert "not_echo" in result.reasons
    assert "crc_ok" in result.reasons
    assert "slave_id_ok" in result.reasons
    assert "function_code_ok" in result.reasons
    assert "byte_count_ok" in result.reasons
    assert "decoded_cell_voltage_0_ok" in result.reasons
    assert result.decoded["slave_id"] == 1
    assert result.decoded["function_code"] == 3
    assert result.decoded["byte_count"] == 2
    assert result.decoded["register_0x1200_raw"] == 3288
    assert result.decoded["cell_voltage_0_mv"] == 3288
    assert result.decoded["cell_voltage_0_v"] == 3.288
    assert result.decoded["decode_status"] == "hardware_confirmed_single_register"
    assert result.decoded["active_cell_voltages_mv"] == [3288]
    assert result.decoded["cell_voltage_min_mv"] == 3288
    assert result.decoded["cell_voltage_max_mv"] == 3288
    assert result.decoded["cell_voltage_delta_mv"] == 0


def test_jk_rs485_modbus_qty8_cell_voltage_block_decodes_trailing_zeros_as_unused():
    profile = JkRs485ModbusProfile()
    probe = {probe.name: probe for probe in profile.probes}[CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME]
    response = _cell_voltage_response([3288, 3287, 3289, 0, 0, 0, 0, 0])

    result = profile.validate_response(probe, response)

    assert result.ok
    assert "decoded_cell_voltage_block_ok" in result.reasons
    assert result.decoded["byte_count"] == 16
    assert result.decoded["decode_status"] == "hardware_confirmed_cell_voltage_block"
    assert result.decoded["cell_voltage_registers_mv"] == [3288, 3287, 3289, 0, 0, 0, 0, 0]
    assert result.decoded["active_cell_voltages_mv"] == [3288, 3287, 3289]
    assert result.decoded["active_cell_voltages_v"] == [3.288, 3.287, 3.289]
    assert result.decoded["active_cell_count"] == 3
    assert result.decoded["unused_register_indices"] == [3, 4, 5, 6, 7]
    assert result.decoded["cell_voltage_min_mv"] == 3287
    assert result.decoded["cell_voltage_max_mv"] == 3289
    assert result.decoded["cell_voltage_delta_mv"] == 2
    assert result.decoded["decode_warnings"] == []


def test_jk_rs485_modbus_qty8_hardware_block_decodes_all_active_cells():
    profile = JkRs485ModbusProfile()
    probe = {probe.name: probe for probe in profile.probes}[CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME]

    result = profile.validate_response(probe, CONFIRMED_RX_QTY8)

    assert result.ok
    assert result.decoded["byte_count"] == 16
    assert result.decoded["cell_voltage_registers_mv"] == [3288, 3287, 3287, 3287, 3288, 3287, 3288, 3288]
    assert result.decoded["active_cell_voltages_mv"] == [3288, 3287, 3287, 3287, 3288, 3287, 3288, 3288]
    assert result.decoded["active_cell_count"] == 8
    assert result.decoded["unused_register_indices"] == []
    assert result.decoded["cell_voltage_min_mv"] == 3287
    assert result.decoded["cell_voltage_max_mv"] == 3288
    assert result.decoded["cell_voltage_delta_mv"] == 1
    assert result.decoded["decode_warnings"] == []


def test_jk_rs485_modbus_qty16_cell_voltage_block_marks_non_trailing_zero_warning():
    profile = JkRs485ModbusProfile()
    probe = {probe.name: probe for probe in profile.probes}[CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME]
    response = _cell_voltage_response([3288, 0, 3286, 3289] + [0] * 12)

    result = profile.validate_response(probe, response)

    assert result.ok
    assert result.decoded["active_cell_voltages_mv"] == [3288, 3286, 3289]
    assert result.decoded["unused_register_indices"] == list(range(4, 16))
    assert result.decoded["cell_voltage_min_mv"] == 3286
    assert result.decoded["cell_voltage_max_mv"] == 3289
    assert result.decoded["cell_voltage_delta_mv"] == 3
    assert "non_trailing_zero_cell_voltage" in result.decoded["decode_warnings"]


def test_jk_rs485_modbus_qty16_hardware_block_decodes_trailing_zeros_as_unused():
    profile = JkRs485ModbusProfile()
    probe = {probe.name: probe for probe in profile.probes}[CONFIRMED_CELL_BLOCK_0_15_PROBE_NAME]

    result = profile.validate_response(probe, CONFIRMED_RX_QTY16)

    assert result.ok
    assert result.decoded["byte_count"] == 32
    assert result.decoded["cell_voltage_registers_mv"] == [
        3287,
        3287,
        3287,
        3287,
        3287,
        3287,
        3288,
        3287,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    assert result.decoded["active_cell_voltages_mv"] == [3287, 3287, 3287, 3287, 3287, 3287, 3288, 3287]
    assert result.decoded["active_cell_count"] == 8
    assert result.decoded["unused_register_indices"] == list(range(8, 16))
    assert result.decoded["cell_voltage_min_mv"] == 3287
    assert result.decoded["cell_voltage_max_mv"] == 3288
    assert result.decoded["cell_voltage_delta_mv"] == 1
    assert result.decoded["decode_warnings"] == []


def test_jk_rs485_modbus_write_function_codes_blocked():
    profile = JkRs485ModbusProfile()

    assert not any(probe.function_code in FORBIDDEN_FUNCTION_CODES for probe in profile.probes)
    for function_code in FORBIDDEN_FUNCTION_CODES:
        try:
            build_modbus_read_request(1, function_code, 0x1200, 1)
        except ValueError as exc:
            assert "only FC03/FC04" in str(exc)
        else:
            raise AssertionError(f"write/control function code allowed: 0x{function_code:02X}")


def test_jk_rs485_modbus_exception_response_is_negative_match():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]
    exception_response = append_crc(bytes.fromhex("01 83 02"))

    result = profile.validate_response(probe, exception_response)

    assert not result.ok
    assert "modbus_exception_response" in result.reasons
    assert "exception_code_02" in result.reasons
    assert result.decoded["crc_status"] == "verified"


def test_jk_rs485_modbus_echo_rejected():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]

    result = profile.validate_response(probe, probe.tx)

    assert not result.ok
    assert "echoed_request" in result.reasons


def test_jk_rs485_modbus_wrong_slave_rejected():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]
    wrong_slave = append_crc(bytes.fromhex("02 03 02 0C D8"))

    result = profile.validate_response(probe, wrong_slave)

    assert not result.ok
    assert "slave_id_mismatch" in result.reasons


def test_jk_rs485_modbus_wrong_function_rejected():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]
    wrong_function = append_crc(bytes.fromhex("01 04 02 0C D8"))

    result = profile.validate_response(probe, wrong_function)

    assert not result.ok
    assert "function_code_mismatch" in result.reasons


def test_jk_rs485_modbus_wrong_byte_count_rejected():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]
    wrong_byte_count = append_crc(bytes.fromhex("01 03 04 0C D8"))

    result = profile.validate_response(probe, wrong_byte_count)

    assert not result.ok
    assert "byte_count_mismatch" in result.reasons


def test_jk_rs485_modbus_extra_payload_byte_rejected():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]
    extra_byte = append_crc(bytes.fromhex("01 03 02 0C D8 00"))

    result = profile.validate_response(probe, extra_byte)

    assert not result.ok
    assert "response_length_mismatch" in result.reasons


def test_jk_rs485_modbus_corrupted_crc_rejected():
    profile = JkRs485ModbusProfile()
    probe = profile.probes[0]
    corrupted = bytearray(CONFIRMED_RX)
    corrupted[-1] ^= 0xFF

    result = profile.validate_response(probe, bytes(corrupted))

    assert not result.ok
    assert "crc_invalid" in result.reasons


def test_jk_rs485_modbus_is_not_jk_pylon_emulation():
    profile = JkRs485ModbusProfile()
    active_profiles = {profile.id: profile for profile in get_all_profiles()}

    assert profile.id != "jk_pylon_lv_emulation"
    assert active_profiles["jk_pylon_lv_emulation"].probes[0].tx.startswith(b"~")
    assert profile.probes[0].tx == CONFIRMED_TX
    assert not profile.probes[0].tx.startswith(b"~")


def test_jk_rs485_modbus_probe_alias_and_canonical_name_work():
    profile = JkRs485ModbusProfile()

    canonical = select_safe_probe(profile, CONFIRMED_PROBE_NAME)
    alias = select_safe_probe(profile, CONFIRMED_PROBE_ALIAS)

    assert canonical.name == CONFIRMED_PROBE_NAME
    assert alias.name == CONFIRMED_PROBE_NAME
    assert canonical.tx == alias.tx == CONFIRMED_TX


def test_jk_modbus_detects_profile_when_primary_probe_answers():
    profile = JkRs485ModbusProfile()
    transport = FakeSerialTransport([CONFIRMED_RX, None, None])

    result = run_active_probe(transport, "FAKE0", profile)

    assert transport.writes == [CONFIRMED_TX, CONFIRMED_TX_QTY8, CONFIRMED_TX_QTY16]
    assert result.detected
    assert result.status == "detected"
    assert result.score >= 80
    assert result.decoded[CONFIRMED_PROBE_NAME]["cell_voltage_0_mv"] == 3288


def test_jk_modbus_scanner_surfaces_non_trailing_zero_decode_warning():
    profile = JkRs485ModbusProfile()
    qty8_response = _cell_voltage_response([3288, 0, 3287, 0, 0, 0, 0, 0])
    transport = FakeSerialTransport([None, qty8_response, None])

    result = run_active_probe(transport, "FAKE0", profile)

    assert result.detected
    assert result.status == "detected"
    assert any(
        f"{CONFIRMED_CELL_BLOCK_0_7_PROBE_NAME}: non_trailing_zero_cell_voltage" == warning
        for warning in result.warnings
    )


def test_jk_modbus_single_probe_cli_prints_decode_and_writes_json_log(capsys, tmp_path):
    transport = FakeSerialTransport([CONFIRMED_RX])

    code = main_cli.run_cli(
        _args(
            [
                "--single-probe",
                "--profile",
                "jk_rs485_modbus",
                "--probe",
                CONFIRMED_PROBE_ALIAS,
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
    assert "Profile: jk_rs485_modbus" in out
    assert f"Probe: {CONFIRMED_PROBE_NAME}" in out
    assert f"TX HEX: {CONFIRMED_TX_HEX}" in out
    assert f"RX HEX: {CONFIRMED_RX_HEX}" in out
    assert "Frames found: 1" in out
    assert "Decoded:" in out
    assert "- register_0x1200_raw: 3288" in out
    assert "- cell_voltage_0_mv: 3288" in out
    assert "- cell_voltage_0_v: 3.288" in out
    assert "Hardware status:" in out
    assert "- confirmed_single_probe" in out

    log_path = next(tmp_path.glob("single_probe_jk_rs485_modbus_read_cell_voltage_0_addr1_*.json"))
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    entry = payload["entries"][0]
    assert entry["tx_hex"] == CONFIRMED_TX_HEX
    assert entry["rx_hex"] == CONFIRMED_RX_HEX
    assert entry["decoded"]["slave_id"] == 1
    assert entry["decoded"]["function_code"] == 3
    assert entry["decoded"]["byte_count"] == 2
    assert entry["decoded"]["register_0x1200_raw"] == 3288
    assert entry["decoded"]["cell_voltage_0_mv"] == 3288
    assert entry["decoded"]["cell_voltage_0_v"] == 3.288
    assert entry["decoded"]["decode_status"] == "hardware_confirmed_single_register"
