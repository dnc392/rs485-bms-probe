from __future__ import annotations

import time

import serial

from core.models import SerialSettings


class SerialPortError(Exception):
    """OS/driver level serial port error."""


class SerialTransport:
    def __init__(self) -> None:
        self.ser: serial.Serial | None = None

    def open(self, port: str, settings: SerialSettings) -> None:
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=settings.baudrate,
                parity=settings.parity,
                bytesize=settings.bytesize,
                stopbits=settings.stopbits,
                timeout=settings.timeout,
            )
        except (OSError, serial.SerialException) as exc:
            raise SerialPortError(str(exc)) from exc

    def close(self) -> None:
        if self.ser:
            self.ser.close()
            self.ser = None

    def write(self, data: bytes) -> None:
        if not self.ser:
            raise RuntimeError("Serial port is not open")
        try:
            self.ser.write(data)
        except (OSError, serial.SerialException) as exc:
            raise SerialPortError(str(exc)) from exc

    def read_for(self, timeout_ms: int) -> bytes:
        if not self.ser:
            raise RuntimeError("Serial port is not open")
        deadline = time.time() + (timeout_ms / 1000)
        buf = bytearray()
        while time.time() < deadline:
            try:
                chunk = self.ser.read(512)
            except (OSError, serial.SerialException) as exc:
                raise SerialPortError(str(exc)) from exc
            if chunk:
                buf.extend(chunk)
        return bytes(buf)

    def actual_settings(self) -> dict[str, object]:
        if not self.ser:
            raise RuntimeError("Serial port is not open")
        return {
            "port": self.ser.port,
            "baudrate": self.ser.baudrate,
            "bytesize": self.ser.bytesize,
            "parity": self.ser.parity,
            "stopbits": self.ser.stopbits,
            "timeout": self.ser.timeout,
        }
