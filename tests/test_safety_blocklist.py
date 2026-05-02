from core.models import ProbeMessage
from core.safety import is_probe_allowed


def test_forbidden_risk_blocked():
    p = ProbeMessage("set_address", b"00", None, 100, "write_forbidden")
    ok, _ = is_probe_allowed(p)
    assert not ok
