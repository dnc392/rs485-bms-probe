from protocols.jk_pylon_lv import JkPylonLvProfile
from protocols.pylon_lv_rs485 import PylonLvProfile


def get_all_profiles():
    return [PylonLvProfile(), JkPylonLvProfile()]
