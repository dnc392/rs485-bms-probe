from pathlib import Path

from core.models import ProbeMessage
from core.report import save_json, save_raw, save_txt
from core.scanner import run_active_probe
from protocols.daly_uart_485 import DalyUart485Profile
from protocols.jbd_jiabaida import JbdXiaoxiangProfile
from protocols.pylon_lv_rs485 import PylonLvProfile
from transport.fake_serial_transport import FakeSerialTransport


JBD_VALID_BASIC_RESPONSE = bytes.fromhex(
    "DD 03 00 1B 17 00 00 00 02 D0 03 E8 00 00 20 78 00 00 00 00 00 00 10 48 03 0F 02 0B 76 0B 82 FB FF 77"
)
DALY_VALID_0X90_RESPONSE = bytes.fromhex("A5 01 90 08 01 02 03 04 05 06 07 08 62")


def _profile_with_forbidden_probe() -> PylonLvProfile:
    p = PylonLvProfile()
    p.probes.append(
        ProbeMessage(
            name="write_register_forbidden",
            tx=b"~deadbeef\r",
            expected_response=None,
            timeout_ms=100,
            risk="write_forbidden",
        )
    )
    return p


def test_scanner_sends_only_allowed_probes_and_blocks_forbidden():
    profile = _profile_with_forbidden_probe()
    transport = FakeSerialTransport(
        responses=[
            b"~20024600800800000000FC22\r",
            b"~20024600D01270805460064006A4C0F9E5\r",
            None,
        ]
    )

    result = run_active_probe(transport=transport, port="FAKE0", profile=profile)

    assert len(transport.writes) == 3  # only original safe probes sent
    assert all(b"deadbeef" not in tx for tx in transport.writes)
    assert any("forbidden risk" in w for w in result.warnings)


def test_valid_response_increases_score_and_noise_is_parsed():
    profile = PylonLvProfile()
    transport = FakeSerialTransport(
        responses=[
            b"noise~20024600800800000000FC22\r",
            b"~BAD24600800800000000FC22\r",
            b"",
        ]
    )

    result = run_active_probe(transport=transport, port="FAKE0", profile=profile)

    assert result.score >= 80
    assert result.status == "detected"
    assert result.detected
    assert any("expected_prefix_ok" in r for r in result.reasons)
    assert any("expected_prefix_mismatch" in r for r in result.reasons)
    assert any("timeout/no frame" in w for w in result.warnings)


def test_timeout_creates_warning_and_no_crash():
    profile = PylonLvProfile()
    transport = FakeSerialTransport(responses=[None, None, None])

    result = run_active_probe(transport=transport, port="FAKE0", profile=profile)

    assert result.score == -50
    assert result.status == "timeout"
    assert not result.detected
    assert len(result.warnings) >= 3
    assert any("timeout/no frame" in w for w in result.warnings)


def test_daly_detects_when_only_primary_probe_responds():
    profile = DalyUart485Profile()
    transport = FakeSerialTransport([DALY_VALID_0X90_RESPONSE] + [None] * 8)

    result = run_active_probe(transport=transport, port="FAKE0", profile=profile)

    assert len(transport.writes) == 9
    assert transport.writes[0][2] == 0x90
    assert result.detected
    assert result.status == "detected"
    assert result.score >= 80
    assert result.raw_score >= 80
    assert len([warning for warning in result.warnings if "timeout/no frame" in warning]) == 8


def test_jbd_detects_when_only_basic_info_responds():
    profile = JbdXiaoxiangProfile()
    transport = FakeSerialTransport([JBD_VALID_BASIC_RESPONSE, None])

    result = run_active_probe(transport=transport, port="FAKE0", profile=profile)

    assert len(transport.writes) == 2
    assert transport.writes[0] == bytes.fromhex("DD A5 03 00 FF FD 77")
    assert result.detected
    assert result.status == "detected"
    assert result.score >= 80
    assert result.raw_score >= 80
    assert any("read_cell_voltages: timeout/no frame" in warning for warning in result.warnings)


def test_report_files_created(tmp_path: Path):
    profile = PylonLvProfile()
    transport = FakeSerialTransport(responses=[b"~20024600800800000000FC22\r", b"", b""])
    result = run_active_probe(transport=transport, port="FAKE0", profile=profile)

    json_path = tmp_path / "report.json"
    txt_path = tmp_path / "report.txt"
    raw_path = tmp_path / "report.raw.txt"

    save_json(result, json_path)
    save_txt(result, txt_path)
    save_raw(result, raw_path)

    assert json_path.exists()
    assert txt_path.exists()
    assert raw_path.exists()
