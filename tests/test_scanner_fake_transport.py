from pathlib import Path

from core.models import ProbeMessage
from core.report import save_json, save_raw, save_txt
from core.scanner import run_active_probe
from protocols.pylon_lv_rs485 import PylonLvProfile
from transport.fake_serial_transport import FakeSerialTransport


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

    assert result.score < 0  # includes corrupted + timeout penalties
    assert any("expected_prefix_ok" in r for r in result.reasons)
    assert any("expected_prefix_mismatch" in r for r in result.reasons)


def test_timeout_creates_warning_and_no_crash():
    profile = PylonLvProfile()
    transport = FakeSerialTransport(responses=[None, None, None])

    result = run_active_probe(transport=transport, port="FAKE0", profile=profile)

    assert result.score <= -150
    assert len(result.warnings) >= 3
    assert any("timeout/no frame" in w for w in result.warnings)


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
