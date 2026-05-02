from __future__ import annotations

import time

from core.models import ScanResult
from core.scorer import detected_from_score
from core.safety import is_probe_allowed
from protocols.base import ProtocolProfile
from transport.serial_transport import SerialTransport


def _status_from_score(score: int, had_timeout: bool) -> str:
    if had_timeout and score < 50:
        return "timeout"
    if score >= 80:
        return "detected"
    if score >= 50:
        return "possible"
    return "not_detected"


def run_active_probe(
    transport: SerialTransport,
    port: str,
    profile: ProtocolProfile,
    include_unverified: bool = False,
) -> ScanResult:
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []
    decoded: dict = {}
    raw_tx: list[str] = []
    raw_rx: list[str] = []
    skipped_probes: list[dict[str, str]] = []
    had_timeout = False

    settings = profile.serial_candidates[0]
    transport.open(port, settings)
    try:
        for probe in profile.probes:
            allowed, reason = is_probe_allowed(probe, include_unverified=include_unverified)
            if not allowed:
                blocked_reason = reason or "blocked"
                warnings.append(blocked_reason)
                skipped_probes.append({"probe": probe.name, "reason": blocked_reason})
                continue
            start = time.time()
            transport.write(probe.tx)
            raw_tx.append(probe.tx.hex(" "))
            rx = transport.read_for(probe.timeout_ms)
            elapsed = int((time.time() - start) * 1000)
            frames = profile.split_frames(rx)
            if not frames:
                had_timeout = True
                score -= 50
                timeout_reason = f"{probe.name}: timeout/no frame"
                reasons.append(timeout_reason)
                warnings.append(timeout_reason)
                continue
            for frame in frames:
                raw_rx.append(frame.hex(" "))
                v = profile.validate_response(probe, frame)
                score += v.score_delta
                if elapsed <= probe.timeout_ms:
                    score += 10
                    reasons.append(f"{probe.name}: within timeout")
                reasons.extend([f"{probe.name}: {r}" for r in v.reasons])
                decoded[probe.name] = v.decoded
    finally:
        transport.close()

    status = _status_from_score(score, had_timeout)
    return ScanResult(
        protocol_id=profile.id,
        protocol_name=profile.name,
        port=port,
        serial_settings=settings.__dict__,
        score=score,
        detected=detected_from_score(score),
        status=status,
        reasons=reasons,
        decoded=decoded,
        raw_tx=raw_tx,
        raw_rx=raw_rx,
        warnings=warnings,
        skipped_probes=skipped_probes,
    )


def run_passive_listen(transport: SerialTransport, port: str, settings, seconds: int = 10) -> dict:
    transport.open(port, settings)
    start = time.time()
    buf = bytearray()
    try:
        while time.time() - start < seconds:
            buf.extend(transport.read_for(200))
    finally:
        transport.close()
    return {"bytes": len(buf), "raw_hex": bytes(buf).hex(" ")}
