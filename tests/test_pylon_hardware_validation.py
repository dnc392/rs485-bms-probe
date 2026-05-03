from pathlib import Path

import pytest

from core.scanner import run_active_probe
import main_cli
from protocols import get_all_profiles
from protocols.pylon_lv_rs485 import PylonLvProfile
from transport.fake_serial_transport import FakeSerialTransport


SAMPLES_DIR = Path(__file__).resolve().parent / "samples" / "hardware"


def _escaped_ascii(value: str) -> bytes:
    return value.replace("\\r", "\r").encode("ascii")


def _sample_rx(name: str) -> bytes:
    text = (SAMPLES_DIR / name).read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("RX: "):
            return _escaped_ascii(line.removeprefix("RX: "))
    raise AssertionError(f"RX not found in {name}")


def _probe(profile: PylonLvProfile, name: str):
    for probe in profile.probes:
        if probe.name == name:
            return probe
    raise AssertionError(f"Probe not found: {name}")


@pytest.mark.parametrize(
    "sample_name",
    [
        "pylon_0x61_analog_1.txt",
        "pylon_0x61_analog_2.txt",
        "pylon_0x61_analog_3.txt",
        "pylon_0x61_analog_4.txt",
    ],
)
def test_valid_hardware_0x61_frames_pass_validation(sample_name: str):
    profile = PylonLvProfile()
    result = profile.validate_response(_probe(profile, "read_system_analog_data"), _sample_rx(sample_name))

    assert result.ok
    assert result.score_delta == 60
    assert "frame_start_ok" in result.reasons
    assert "frame_end_ok" in result.reasons
    assert "ascii_hex_payload_ok" in result.reasons
    assert "expected_prefix_ok" in result.reasons
    assert "not_echo" in result.reasons
    assert "plausible_length_ok" in result.reasons
    assert "checksum_ok" in result.reasons
    assert result.decoded["parse_status"] == "partial"
    assert result.decoded["checksum_status"] == "verified"


def test_valid_hardware_0x62_frame_passes_validation():
    profile = PylonLvProfile()
    result = profile.validate_response(
        _probe(profile, "read_system_alarm_info"),
        _sample_rx("pylon_0x62_alarm_status.txt"),
    )

    assert result.ok
    assert result.score_delta == 60
    assert result.decoded["checksum_status"] == "verified"


def test_valid_hardware_0x63_frame_passes_validation():
    profile = PylonLvProfile()
    result = profile.validate_response(
        _probe(profile, "read_charge_discharge_management"),
        _sample_rx("pylon_0x63_charge_discharge.txt"),
    )

    assert result.ok
    assert result.score_delta == 60
    assert result.decoded["checksum_status"] == "verified"


def test_corrupted_prefix_fails_validation():
    profile = PylonLvProfile()
    frame = b"~BAD24600800800000000FC22\r"
    result = profile.validate_response(_probe(profile, "read_system_alarm_info"), frame)

    assert not result.ok
    assert result.score_delta < 0
    assert "expected_prefix_mismatch" in result.reasons


def test_missing_cr_fails_validation():
    profile = PylonLvProfile()
    frame = b"~20024600800800000000FC22"
    result = profile.validate_response(_probe(profile, "read_system_alarm_info"), frame)

    assert not result.ok
    assert result.score_delta < 0
    assert "frame_end_missing" in result.reasons


def test_lowercase_hex_fails_validation():
    profile = PylonLvProfile()
    frame = b"~20024600800800000000fc22\r"
    result = profile.validate_response(_probe(profile, "read_system_alarm_info"), frame)

    assert not result.ok
    assert result.score_delta < 0
    assert "ascii_hex_payload_invalid" in result.reasons


def test_non_hex_payload_fails_validation():
    profile = PylonLvProfile()
    frame = b"~20024600800800000000ZZ22\r"
    result = profile.validate_response(_probe(profile, "read_system_alarm_info"), frame)

    assert not result.ok
    assert result.score_delta < 0
    assert "ascii_hex_payload_invalid" in result.reasons


def test_exact_echo_fails_with_strong_negative_score():
    profile = PylonLvProfile()
    probe = _probe(profile, "read_system_alarm_info")
    result = profile.validate_response(probe, probe.tx)

    assert not result.ok
    assert result.score_delta <= -100
    assert "echoed_request" in result.reasons


def test_scan_score_is_capped_but_raw_score_remains_cumulative():
    profile = PylonLvProfile()
    transport = FakeSerialTransport(
        responses=[
            _sample_rx("pylon_0x61_analog_1.txt"),
            _sample_rx("pylon_0x62_alarm_status.txt"),
            _sample_rx("pylon_0x63_charge_discharge.txt"),
        ]
    )

    result = run_active_probe(transport, "FAKE0", profile)

    assert result.score == 100
    assert result.raw_score == 210
    assert result.status == "detected"


def test_scan_cli_prints_score_and_raw_score(monkeypatch, capsys, tmp_path: Path):
    profile = PylonLvProfile()
    transport = FakeSerialTransport(
        responses=[
            _sample_rx("pylon_0x61_analog_1.txt"),
            _sample_rx("pylon_0x62_alarm_status.txt"),
            _sample_rx("pylon_0x63_charge_discharge.txt"),
        ]
    )
    monkeypatch.setattr(main_cli, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(main_cli, "LOGS_DIR", tmp_path / "logs")

    code = main_cli.run_cli(
        main_cli.build_parser().parse_args(["--scan", "--port", "FAKE0", "--profiles", profile.id]),
        transport_factory=lambda: transport,
        list_ports_func=lambda: ["FAKE0"],
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "pylon_lv_rs485: score=100 raw_score=210 status=detected" in out


def test_active_registry_contains_only_pylon_profiles_for_hardware_validation():
    assert {profile.id for profile in get_all_profiles()} == {
        "pylon_lv_rs485",
        "jk_pylon_lv_emulation",
    }
