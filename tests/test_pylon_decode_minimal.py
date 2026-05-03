from pathlib import Path

from protocols.pylon_lv_rs485 import PylonLvProfile


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


def test_0x62_alarm_status_minimal_decode():
    profile = PylonLvProfile()
    result = profile.validate_response(
        _probe(profile, "read_system_alarm_info"),
        _sample_rx("pylon_0x62_alarm_status.txt"),
    )

    decoded = result.decoded
    assert decoded["parse_status"] == "partial"
    assert decoded["checksum_status"] == "verified"
    assert decoded["checksum_received"] == "FC22"
    assert decoded["checksum_calculated"] == "FC22"
    assert decoded["response_type"] == "system_alarm_status"
    assert decoded["system_alarm_status_1"]["raw_hex"] == "00"
    assert not any(decoded["system_alarm_status_1"]["flags"].values())
    assert decoded["system_alarm_status_2"]["unknown_bits"] == [3, 2, 1, 0]
    assert decoded["system_protection_status_2"]["unknown_bits"] == [7, 4, 2, 1, 0]


def test_0x63_charge_discharge_management_minimal_decode():
    profile = PylonLvProfile()
    result = profile.validate_response(
        _probe(profile, "read_charge_discharge_management"),
        _sample_rx("pylon_0x63_charge_discharge.txt"),
    )

    decoded = result.decoded
    assert decoded["parse_status"] == "partial"
    assert decoded["checksum_status"] == "verified"
    assert decoded["checksum_received"] == "F9E5"
    assert decoded["checksum_calculated"] == "F9E5"
    assert decoded["response_type"] == "charge_discharge_management"
    assert decoded["charge_voltage_limit_v"] == 28.8
    assert decoded["discharge_voltage_limit_v"] == 21.6
    assert decoded["charge_current_limit_a"] == 160.0
    assert decoded["discharge_current_limit_a"] == 170.0
    assert decoded["charge_discharge_status"]["raw_hex"] == "C0"
    assert decoded["charge_discharge_status"]["flags"]["charge_enable"]
    assert decoded["charge_discharge_status"]["flags"]["discharge_enable"]
    assert not decoded["charge_discharge_status"]["flags"]["charge_immediately"]
    assert not decoded["charge_discharge_status"]["flags"]["full_charge_request"]


def test_0x61_analog_data_partial_decode():
    profile = PylonLvProfile()
    result = profile.validate_response(
        _probe(profile, "read_system_analog_data"),
        _sample_rx("pylon_0x61_analog_4.txt"),
    )

    decoded = result.decoded
    assert decoded["parse_status"] == "partial"
    assert decoded["checksum_status"] == "verified"
    assert decoded["checksum_received"] == "E999"
    assert decoded["checksum_calculated"] == "E999"
    assert decoded["response_type"] == "system_analog_data"
    assert decoded["system_total_average_voltage_v"] == 26.298
    assert decoded["system_total_current_a"] == 0.0
    assert decoded["system_soc_percent"] == 66
    assert decoded["average_soh_percent"] == 100
    assert decoded["minimum_soh_percent"] == 100
    assert decoded["highest_cell_voltage_v"] == 3.288
    assert decoded["lowest_cell_voltage_v"] == 3.287
    assert decoded["average_cell_temperature_c"] == 17.0
    assert decoded["highest_cell_temperature_c"] == 17.1
    assert decoded["undecoded_tail_hex"]
