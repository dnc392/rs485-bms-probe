from pathlib import Path

from core.diagnostics import parse_tx_ascii, parse_tx_hex, run_passive_capture
from core.models import SerialSettings
import main_cli
from main_cli import build_parser, run_cli
from protocols import get_all_profiles
from transport.fake_serial_transport import FakeSerialTransport


PYLON_ALARM_TX_HEX = "7E 32 30 31 32 34 36 36 32 30 30 30 30 46 44 41 39 0D"
PYLON_RESPONSE = b"~20024600800800000000FC22\r"


def _args(argv: list[str]):
    return build_parser().parse_args(argv)


def test_doctor_command_smoke(capsys, tmp_path: Path):
    transport = FakeSerialTransport(responses=[])

    code = run_cli(
        _args(["--doctor", "--port", "COM3", "--baud", "9600"]),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["COM3"],
        log_dir=tmp_path,
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "Available ports:" in out
    assert "Selected port exists: yes (COM3)" in out
    assert "Open: OK" in out
    assert "Close: OK" in out
    assert "only proves OS-level port access" in out


def test_single_probe_prints_tx_hex_and_rx_len(capsys, tmp_path: Path):
    transport = FakeSerialTransport(responses=[PYLON_RESPONSE])

    code = run_cli(
        _args(
            [
                "--single-probe",
                "--port",
                "COM3",
                "--baud",
                "9600",
                "--profile",
                "pylon_lv_rs485",
                "--probe",
                "read_system_alarm_info",
                "--timeout-ms",
                "1500",
            ]
        ),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["COM3"],
        log_dir=tmp_path,
    )

    out = capsys.readouterr().out
    assert code == 0
    assert f"TX HEX: {PYLON_ALARM_TX_HEX}" in out
    assert f"RX LEN: {len(PYLON_RESPONSE)}" in out
    assert "Frames found: 1" in out
    assert list(tmp_path.glob("single_probe_pylon_lv_rs485_read_system_alarm_info_*.json"))


def test_tx_ascii_converts_escaped_cr_to_0d(capsys, tmp_path: Path):
    transport = FakeSerialTransport(responses=[b""])

    code = run_cli(
        _args(["--tx-ascii", "~201246620000FDA9\\r", "--port", "COM3", "--baud", "9600"]),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["COM3"],
        log_dir=tmp_path,
    )

    out = capsys.readouterr().out
    assert code == 0
    assert parse_tx_ascii("~201246620000FDA9\\r") == bytes.fromhex(PYLON_ALARM_TX_HEX)
    assert f"TX HEX: {PYLON_ALARM_TX_HEX}" in out
    assert "Manual TX mode bypasses profile selection" in out


def test_tx_hex_parses_spaced_hex(capsys, tmp_path: Path):
    transport = FakeSerialTransport(responses=[b""])

    code = run_cli(
        _args(["--tx-hex", PYLON_ALARM_TX_HEX, "--port", "COM3", "--baud", "9600"]),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["COM3"],
        log_dir=tmp_path,
    )

    capsys.readouterr()
    assert code == 0
    assert parse_tx_hex(PYLON_ALARM_TX_HEX) == bytes.fromhex(PYLON_ALARM_TX_HEX)
    assert transport.writes == [bytes.fromhex(PYLON_ALARM_TX_HEX)]


def test_repeat_sends_exact_number_of_selected_frames(tmp_path: Path):
    transport = FakeSerialTransport(responses=[b"", b"", b""])

    code = run_cli(
        _args(
            [
                "--single-probe",
                "--port",
                "COM3",
                "--baud",
                "9600",
                "--profile",
                "pylon_lv_rs485",
                "--probe",
                "read_system_alarm_info",
                "--repeat",
                "3",
                "--delay-ms",
                "0",
            ]
        ),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["COM3"],
        log_dir=tmp_path,
    )

    assert code == 0
    assert transport.writes == [bytes.fromhex(PYLON_ALARM_TX_HEX)] * 3


def test_passive_sends_zero_writes():
    transport = FakeSerialTransport(responses=[b"unused"])

    run_passive_capture(
        transport=transport,
        port="COM3",
        settings=SerialSettings(baudrate=9600),
        seconds=0,
    )

    assert transport.writes == []


def test_active_registry_contains_only_pylon_profiles():
    assert {profile.id for profile in get_all_profiles()} == {
        "pylon_lv_rs485",
        "jk_pylon_lv_emulation",
    }


def test_runtime_error_is_reported_as_internal(monkeypatch, capsys):
    def fail(_args):
        raise RuntimeError("broken invariant")

    monkeypatch.setattr(main_cli, "run_cli", fail)

    code = main_cli.main(["--list-profiles"])

    out = capsys.readouterr().out
    assert code == 1
    assert "Internal error: broken invariant" in out
    assert "COM port busy or access denied" not in out


def test_scan_report_paths_do_not_depend_on_cwd(monkeypatch, tmp_path: Path):
    output_base = tmp_path / "package_dir"
    reports_dir = output_base / "reports"
    logs_dir = output_base / "logs"
    unrelated_cwd = tmp_path / "unrelated_cwd"
    unrelated_cwd.mkdir()

    monkeypatch.setattr(main_cli, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(main_cli, "LOGS_DIR", logs_dir)
    monkeypatch.chdir(unrelated_cwd)

    transport = FakeSerialTransport(responses=[PYLON_RESPONSE, PYLON_RESPONSE, PYLON_RESPONSE])

    code = main_cli.run_cli(
        _args(["--scan", "--port", "COM3", "--profiles", "pylon_lv_rs485"]),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["COM3"],
    )

    assert code == 0
    assert reports_dir.is_dir()
    assert logs_dir.is_dir()
    assert (reports_dir / "pylon_lv_rs485.json").is_file()
    assert (reports_dir / "pylon_lv_rs485.txt").is_file()
    assert (logs_dir / "pylon_lv_rs485.raw.log").is_file()
