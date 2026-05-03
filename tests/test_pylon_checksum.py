from pathlib import Path

import pytest

from protocols.pylon_lv_rs485 import PylonLvProfile, verify_pylon_checksum


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
        "pylon_0x62_alarm_status.txt",
        "pylon_0x63_charge_discharge.txt",
    ],
)
def test_checksum_valid_for_captured_hardware_frames(sample_name: str):
    ok, detail = verify_pylon_checksum(_sample_rx(sample_name))

    assert ok
    assert "received=" in detail
    assert "calculated=" in detail


def test_corrupted_last_checksum_digit_fails():
    profile = PylonLvProfile()
    frame = b"~20024600800800000000FC23\r"

    ok, detail = verify_pylon_checksum(frame)
    result = profile.validate_response(_probe(profile, "read_system_alarm_info"), frame)

    assert not ok
    assert "received=FC23 calculated=FC22" in detail
    assert not result.ok
    assert "checksum_invalid" in result.reasons


def test_corrupted_payload_fails_checksum():
    profile = PylonLvProfile()
    frame = b"~20024600800800000001FC22\r"

    ok, detail = verify_pylon_checksum(frame)
    result = profile.validate_response(_probe(profile, "read_system_alarm_info"), frame)

    assert not ok
    assert "received=FC22" in detail
    assert not result.ok
    assert "checksum_invalid" in result.reasons


def test_frame_without_cr_fails_before_checksum():
    profile = PylonLvProfile()
    frame = b"~20024600800800000000FC22"
    result = profile.validate_response(_probe(profile, "read_system_alarm_info"), frame)

    assert not result.ok
    assert "frame_end_missing" in result.reasons
    assert "checksum_not_verified" in result.reasons
    assert "checksum_ok" not in result.reasons
    assert "checksum_invalid" not in result.reasons
