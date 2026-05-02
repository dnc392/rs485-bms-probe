from core.models import ProbeMessage
from core.scanner import run_active_probe
from protocols.pylon_lv_rs485 import PylonLvProfile
from transport.fake_serial_transport import FakeSerialTransport


def test_write_forbidden_never_sent_even_with_include_unverified():
    profile = PylonLvProfile()
    forbidden = ProbeMessage("danger", b"~FFFF\r", None, 50, "write_forbidden")
    profile.probes = [forbidden]

    transport = FakeSerialTransport(responses=[b"~20024600\r"])
    result = run_active_probe(transport, "FAKE0", profile, include_unverified=True)

    assert transport.writes == []
    assert result.skipped_probes[0]["probe"] == "danger"


def test_unknown_risk_blocked_by_default():
    profile = PylonLvProfile()
    unknown = ProbeMessage("mystery", b"~AAAA\r", None, 50, "wake")
    profile.probes = [unknown]

    transport = FakeSerialTransport(responses=[b"~20024600\r"])
    result = run_active_probe(transport, "FAKE0", profile)

    assert transport.writes == []
    assert "unknown risk" in result.skipped_probes[0]["reason"]


def test_unverified_requires_opt_in():
    profile = PylonLvProfile()
    unverified = ProbeMessage("candidate", b"~BBBB\r", None, 50, "unverified_read")
    profile.probes = [unverified]

    transport = FakeSerialTransport(responses=[b"~20024600\r"])
    blocked_result = run_active_probe(transport, "FAKE0", profile, include_unverified=False)
    assert transport.writes == []
    assert "unverified probe disabled" in blocked_result.skipped_probes[0]["reason"]

    transport2 = FakeSerialTransport(responses=[b"~20024600\r"])
    allowed_result = run_active_probe(transport2, "FAKE0", profile, include_unverified=True)
    assert transport2.writes == [b"~BBBB\r"]
    assert allowed_result.skipped_probes == []


def test_skipped_probes_included_in_report_result():
    profile = PylonLvProfile()
    profile.probes = [ProbeMessage("mystery", b"~AAAA\r", None, 50, "wake")]
    transport = FakeSerialTransport(responses=[b""])

    result = run_active_probe(transport, "FAKE0", profile)

    assert result.skipped_probes
    assert result.skipped_probes[0]["probe"] == "mystery"
