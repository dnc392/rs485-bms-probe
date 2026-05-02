import json
from pathlib import Path

from core.models import ScanResult
from core.report import save_json


def test_json_report_valid(tmp_path: Path):
    r = ScanResult("pylon_lv_rs485","Pylon","COM3",{},80,True,"detected",[],{},[],[],[],[])
    p = tmp_path / "r.json"
    save_json(r, p)
    data = json.loads(p.read_text())
    assert data["protocol_id"] == "pylon_lv_rs485"
