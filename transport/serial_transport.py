from __future__ import annotations

import time

import serial

from core.models import SerialSettings


class SerialTransport:
    def __init__(self) -> None:
        self.ser: serial.Serial | None = None

    def open(self, port: str, settings: SerialSettings) -> None:
        self.ser = serial.Serial(
            port=port,
            baudrate=settings.baudrate,
            parity=settings.parity,
            bytesize=settings.bytesize,
            stopbits=settings.stopbits,
            timeout=settings.timeout,
        )

    def close(self) -> None:
        if self.ser:
            self.ser.close()
            self.ser = None

    def write(self, data: bytes) -> None:
        if not self.ser:
            raise RuntimeError("Serial port is not open")
        self.ser.write(data)

    def read_for(self, timeout_ms: int) -> bytes:
        if not self.ser:
            raise RuntimeError("Serial port is not open")
        deadline = time.time() + (timeout_ms / 1000)
        buf = bytearray()
        while time.time() < deadline:
            chunk = self.ser.read(512)
            if chunk:
                buf.extend(chunk)
        return bytes(buf)
