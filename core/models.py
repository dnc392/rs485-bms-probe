from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SerialSettings:
    baudrate: int
    parity: str = "N"
    bytesize: int = 8
    stopbits: int = 1
    timeout: float = 1.0


@dataclass
class ProbeMessage:
    name: str
    tx: bytes
    expected_response: bytes | None
    timeout_ms: int
    risk: str
    description: str = ""
    slave_id: int | None = None
    function_code: int | None = None
    start_register: int | None = None
    quantity: int | None = None
    primary: bool = False
    hardware_confirmed: bool = False
    aliases: tuple[str, ...] = ()

    @property
    def request_hex(self) -> str:
        return self.tx.hex(" ").upper()


@dataclass
class ValidationResult:
    ok: bool
    score_delta: int
    reasons: list[str] = field(default_factory=list)
    decoded: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanResult:
    protocol_id: str
    protocol_name: str
    port: str
    serial_settings: dict[str, Any]
    score: int
    raw_score: int
    detected: bool
    status: str
    reasons: list[str]
    decoded: dict[str, Any]
    raw_tx: list[str]
    raw_rx: list[str]
    warnings: list[str]
    skipped_probes: list[dict[str, str]]
