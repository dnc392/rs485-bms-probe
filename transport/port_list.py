from __future__ import annotations

from serial.tools import list_ports


def list_serial_ports() -> list[str]:
    return [p.device for p in list_ports.comports()]
