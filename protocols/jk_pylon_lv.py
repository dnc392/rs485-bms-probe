from __future__ import annotations

from protocols.pylon_lv_rs485 import PylonLvProfile


class JkPylonLvProfile(PylonLvProfile):
    def __init__(self) -> None:
        super().__init__()
        self.id = "jk_pylon_lv_emulation"
        self.name = "JK BMS Pylon LV emulation / Protocol 014"
