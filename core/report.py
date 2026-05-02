from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

from core.models import ScanResult


def save_json(result: ScanResult, path: Path) -> None:
    path.write_text(json.dumps(result.__dict__, indent=2, ensure_ascii=False), encoding="utf-8")


def save_txt(result: ScanResult, path: Path) -> None:
    lines = [
        f"Protocol: {result.protocol_name} ({result.protocol_id})",
        f"Port: {result.port}",
        f"Score: {result.score}",
        f"Detected: {result.detected}",
        "Reasons:",
        *[f"- {r}" for r in result.reasons],
        "Warnings:",
        *[f"- {w}" for w in result.warnings],
        "Skipped probes:",
        *[f"- {item['probe']}: {item['reason']}" for item in result.skipped_probes],
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def save_raw(result: ScanResult, path: Path) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    lines = []
    for x in result.raw_tx:
        lines.append(f"{ts} | PROBE_TX | {x} |")
    for x in result.raw_rx:
        lines.append(f"{ts} | PROBE_RX | {x} |")
    path.write_text("\n".join(lines), encoding="utf-8")
