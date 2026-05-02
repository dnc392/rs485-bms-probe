from __future__ import annotations

from core.models import ProbeMessage, SerialSettings, ValidationResult
from protocols.base import ProtocolProfile

EXPECTED_PREFIX = b"~200246"


def _probe(name: str, tx_ascii: str) -> ProbeMessage:
    return ProbeMessage(name=name, tx=tx_ascii.encode("ascii"), expected_response=EXPECTED_PREFIX, timeout_ms=500, risk="safe_read")


class PylonLvProfile(ProtocolProfile):
    def __init__(self) -> None:
        super().__init__(
            id="pylon_lv_rs485",
            name="Pylontech / Pylon LV RS485 ASCII",
            transport="rs485",
            serial_candidates=[SerialSettings(baudrate=9600, parity="N")],
            probes=[
                _probe("read_system_analog_data", "~201246610000FDAA\r"),
                _probe("read_system_alarm_info", "~201246620000FDA9\r"),
                _probe("read_charge_discharge_management", "~201246630000FDA8\r"),
            ],
            confidence_hint=95,
        )

    def split_frames(self, rx_buffer: bytes) -> list[bytes]:
        frames: list[bytes] = []
        for chunk in rx_buffer.split(b"\r"):
            start = chunk.find(b"~")
            if start >= 0:
                candidate = chunk[start:]
                if candidate:
                    frames.append(candidate + b"\r")
        return frames

    def validate_response(self, request: ProbeMessage, frame: bytes) -> ValidationResult:
        score = 0
        reasons: list[str] = []
        if frame.startswith(EXPECTED_PREFIX):
            score += 30
            reasons.append("prefix matched")
        else:
            score -= 50
            reasons.append("prefix mismatch")
        if frame.endswith(b"\r"):
            score += 20
            reasons.append("frame ending matched")
        return ValidationResult(ok=score > 0, score_delta=score, reasons=reasons, decoded=self.decode_response(frame))

    def decode_response(self, frame: bytes) -> dict:
        return {"ascii": frame.decode("ascii", errors="replace").strip()}
