from __future__ import annotations

from collections import deque

from core.models import SerialSettings


class FakeSerialTransport:
    """Deterministic in-memory transport for tests.

    Responses are dequeued on each `read_for` call in the same order as writes.
    """

    def __init__(self, responses: list[bytes | None]) -> None:
        self.responses = deque(responses)
        self.opened = False
        self.port: str | None = None
        self.settings: SerialSettings | None = None
        self.writes: list[bytes] = []

    def open(self, port: str, settings: SerialSettings) -> None:
        self.opened = True
        self.port = port
        self.settings = settings

    def close(self) -> None:
        self.opened = False

    def write(self, data: bytes) -> None:
        if not self.opened:
            raise RuntimeError("Serial port is not open")
        self.writes.append(data)

    def read_for(self, timeout_ms: int) -> bytes:  # noqa: ARG002
        if not self.opened:
            raise RuntimeError("Serial port is not open")
        if not self.responses:
            return b""
        value = self.responses.popleft()
        return b"" if value is None else value
