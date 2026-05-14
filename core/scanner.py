from __future__ import annotations

import time

from core.models import ScanResult
from core.safety import is_probe_allowed
from protocols.base import ProtocolProfile
from transport.serial_transport import SerialTransport

SCAN_BLOCKED_RISKS = {"experimental_unverified_read"}


def _status_from_score(score: int, had_timeout: bool, had_valid_response: bool) -> str:
    if had_valid_response and score < 80:
        return "possible"
    if had_timeout and not had_valid_response:
        return "timeout"
    if score >= 80:
        return "detected"
    if score >= 50:
        return "possible"
    return "not_detected"


def _ordered_probes(profile: ProtocolProfile):
    primary_names = set(profile.primary_probe_names)
    if not primary_names:
        return profile.probes
    primary = [probe for probe in profile.probes if probe.name in primary_names]
    extended = [probe for probe in profile.probes if probe.name not in primary_names]
    return primary + extended


def run_active_probe(
    transport: SerialTransport,
    port: str,
    profile: ProtocolProfile,
    include_unverified: bool = False,
) -> ScanResult:
    per_probe_scores: list[int] = []
    valid_probe_scores: list[int] = []
    reasons: list[str] = []
    warnings: list[str] = []
    decoded: dict = {}
    raw_tx: list[str] = []
    raw_rx: list[str] = []
    skipped_probes: list[dict[str, str]] = []
    had_timeout = False
    had_valid_response = False
    had_primary_valid_response = False

    settings = profile.serial_candidates[0]
    primary_names = set(profile.primary_probe_names)
    transport.open(port, settings)
    try:
        for probe in _ordered_probes(profile):
            if probe.risk in SCAN_BLOCKED_RISKS:
                blocked_reason = "Blocked by scan policy (experimental probe disabled)."
                warnings.append(blocked_reason)
                skipped_probes.append({"probe": probe.name, "reason": blocked_reason})
                continue
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
                per_probe_scores.append(-50)
                timeout_reason = f"{probe.name}: timeout/no frame"
                reasons.append(timeout_reason)
                warnings.append(timeout_reason)
                continue
            for frame in frames:
                raw_rx.append(frame.hex(" "))
                v = profile.validate_response(probe, frame)
                frame_score = v.score_delta
                if elapsed <= probe.timeout_ms:
                    frame_score += 10
                    reasons.append(f"{probe.name}: within timeout")
                per_probe_scores.append(frame_score)
                reasons.extend([f"{probe.name}: {r}" for r in v.reasons])
                if "checksum_invalid" in v.reasons:
                    warnings.append(f"{probe.name}: checksum_invalid")
                if "decoded_sanity_failed" in v.reasons:
                    warnings.append(f"{probe.name}: decoded_sanity_failed")
                for decode_warning in v.decoded.get("decode_warnings", []):
                    warnings.append(f"{probe.name}: {decode_warning}")
                if not v.ok:
                    warnings.append(f"{probe.name}: validation failed")
                else:
                    had_valid_response = True
                    if not primary_names or probe.name in primary_names:
                        had_primary_valid_response = True
                    valid_probe_scores.append(frame_score)
                decoded[probe.name] = v.decoded
    finally:
        transport.close()

    raw_score = max(valid_probe_scores) if valid_probe_scores else max(per_probe_scores, default=0)
    score = min(raw_score, 100)
    if had_primary_valid_response and score < 80:
        score = 80
    elif had_valid_response and score < 50:
        score = 50
    status = _status_from_score(score, had_timeout, had_valid_response)
    return ScanResult(
        protocol_id=profile.id,
        protocol_name=profile.name,
        port=port,
        serial_settings=settings.__dict__,
        score=score,
        raw_score=raw_score,
        detected=had_valid_response,
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
