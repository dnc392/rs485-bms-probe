from __future__ import annotations

from dataclasses import dataclass

from core.models import ProbeMessage, SerialSettings, ValidationResult


@dataclass
class ProtocolProfile:
    id: str
    name: str
    transport: str
    serial_candidates: list[SerialSettings]
    probes: list[ProbeMessage]
    confidence_hint: int = 50
    enabled_by_default: bool = True

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        return [rx_buffer] if rx_buffer else []

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        return ValidationResult(ok=bool(frame), score_delta=10 if frame else -50)

    def decode_response(self, frame: bytes) -> dict:
        return {}
