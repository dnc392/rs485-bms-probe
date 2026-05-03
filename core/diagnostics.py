from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from core.models import ProbeMessage, SerialSettings, ValidationResult
from core.safety import is_probe_allowed
from protocols.base import ProtocolProfile


class Transport(Protocol):
    def open(self, port: str, settings: SerialSettings) -> None:
        ...

    def close(self) -> None:
        ...

    def write(self, data: bytes) -> None:
        ...

    def read_for(self, timeout_ms: int) -> bytes:
        ...


@dataclass
class TransactionEntry:
    attempt: int
    tx_ascii: str
    tx_hex: str
    rx_len: int
    rx_ascii_preview: str
    rx_hex: str
    frames_found: int
    validation_reasons: list[str]


def hex_dump(data: bytes) -> str:
    return data.hex(" ").upper()


def ascii_preview(data: bytes, limit: int = 160) -> str:
    text = data[:limit].decode("ascii", errors="replace")
    text = text.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")
    if len(data) > limit:
        text += "..."
    return text


def parse_tx_ascii(value: str) -> bytes:
    out = bytearray()
    i = 0
    while i < len(value):
        ch = value[i]
        if ch == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt == "r":
                out.append(0x0D)
                i += 2
                continue
            if nxt == "n":
                out.append(0x0A)
                i += 2
                continue
            if nxt == "t":
                out.append(0x09)
                i += 2
                continue
            if nxt == "\\":
                out.append(0x5C)
                i += 2
                continue
        out.extend(ch.encode("ascii"))
        i += 1
    return bytes(out)


def parse_tx_hex(value: str) -> bytes:
    compact = "".join(value.split())
    if len(compact) % 2:
        raise ValueError("hex string must contain an even number of digits")
    try:
        return bytes.fromhex(compact)
    except ValueError as exc:
        raise ValueError("hex string contains non-hex characters") from exc


def extract_ascii_cr_frames(data: bytes) -> list[bytes]:
    frames: list[bytes] = []
    pos = 0
    while True:
        start = data.find(b"~", pos)
        if start < 0:
            return frames
        end = data.find(b"\r", start)
        if end < 0:
            return frames
        frames.append(data[start : end + 1])
        pos = end + 1


def _log_path(log_dir: Path, prefix: str, suffix: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{prefix}_{ts}{suffix}"


def save_transaction_log(
    entries: list[TransactionEntry],
    log_dir: Path,
    prefix: str = "transaction",
) -> Path:
    path = _log_path(log_dir, prefix, ".json")
    payload = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "entries": [asdict(entry) for entry in entries],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def save_raw_log(data: bytes, log_dir: Path, prefix: str = "passive") -> Path:
    path = _log_path(log_dir, prefix, ".raw.bin")
    path.write_bytes(data)
    return path


def select_safe_probe(profile: ProtocolProfile, probe_name: str) -> ProbeMessage:
    for probe in profile.probes:
        if probe.name != probe_name:
            continue
        allowed, reason = is_probe_allowed(probe, include_unverified=False)
        if not allowed:
            raise ValueError(f"Probe is not safe to send: {reason}")
        if probe.risk != "safe_read":
            raise ValueError(f"Probe is not confirmed safe_read: {probe.risk}")
        return probe
    raise ValueError(f"Unknown probe for profile {profile.id}: {probe_name}")


def validate_frames(
    profile: ProtocolProfile,
    probe: ProbeMessage,
    frames: list[bytes],
) -> list[str]:
    if not frames:
        return ["no frames found"]
    reasons: list[str] = []
    for idx, frame in enumerate(frames, start=1):
        result: ValidationResult = profile.validate_response(probe, frame)
        prefix = f"frame {idx}: "
        if result.reasons:
            reasons.extend(prefix + reason for reason in result.reasons)
        else:
            reasons.append(prefix + ("ok" if result.ok else "invalid"))
    return reasons


def run_single_probe_transaction(
    transport: Transport,
    port: str,
    settings: SerialSettings,
    profile: ProtocolProfile,
    probe: ProbeMessage,
    timeout_ms: int,
    repeat: int = 1,
    delay_ms: int = 0,
) -> list[TransactionEntry]:
    if repeat < 1:
        raise ValueError("--repeat must be >= 1")
    if timeout_ms < 1:
        raise ValueError("--timeout-ms must be >= 1")
    if delay_ms < 0:
        raise ValueError("--delay-ms must be >= 0")

    entries: list[TransactionEntry] = []
    transport.open(port, settings)
    try:
        for attempt in range(1, repeat + 1):
            transport.write(probe.tx)
            rx = transport.read_for(timeout_ms)
            frames = profile.split_frames(rx)
            entries.append(
                TransactionEntry(
                    attempt=attempt,
                    tx_ascii=ascii_preview(probe.tx),
                    tx_hex=hex_dump(probe.tx),
                    rx_len=len(rx),
                    rx_ascii_preview=ascii_preview(rx),
                    rx_hex=hex_dump(rx),
                    frames_found=len(frames),
                    validation_reasons=validate_frames(profile, probe, frames),
                )
            )
            if attempt < repeat and delay_ms:
                time.sleep(delay_ms / 1000)
    finally:
        transport.close()
    return entries


def run_manual_transaction(
    transport: Transport,
    port: str,
    settings: SerialSettings,
    tx: bytes,
    timeout_ms: int,
) -> TransactionEntry:
    if timeout_ms < 1:
        raise ValueError("--timeout-ms must be >= 1")
    transport.open(port, settings)
    try:
        transport.write(tx)
        rx = transport.read_for(timeout_ms)
    finally:
        transport.close()
    frames = extract_ascii_cr_frames(rx)
    return TransactionEntry(
        attempt=1,
        tx_ascii=ascii_preview(tx),
        tx_hex=hex_dump(tx),
        rx_len=len(rx),
        rx_ascii_preview=ascii_preview(rx),
        rx_hex=hex_dump(rx),
        frames_found=len(frames),
        validation_reasons=["manual mode: profile validation bypassed"],
    )


def run_passive_capture(
    transport: Transport,
    port: str,
    settings: SerialSettings,
    seconds: int,
) -> bytes:
    if seconds < 0:
        raise ValueError("--seconds must be >= 0")
    transport.open(port, settings)
    start = time.time()
    buf = bytearray()
    try:
        while time.time() - start < seconds:
            buf.extend(transport.read_for(200))
    finally:
        transport.close()
    return bytes(buf)
