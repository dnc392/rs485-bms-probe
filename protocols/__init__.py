from protocols.daly_uart_485 import DalyUart485Profile
from protocols.growatt_bms_rs485_1xsxxp import GrowattBmsRs4851xSxxpProfile
from protocols.jbd_jiabaida import JbdXiaoxiangProfile
from protocols.jk_pylon_lv import JkPylonLvProfile
from protocols.jk_rs485_modbus import JkRs485ModbusProfile
from protocols.pace_rs485_modbus_v1_3 import PaceRs485ModbusV13Profile
from protocols.pylon_lv_rs485 import PylonLvProfile
from protocols.voltronic_inverter_bms_485 import VoltronicInverterBms485Profile
from protocols.wow_rs485_modbus_v1_3 import WowRs485ModbusV13Profile


def get_all_profiles():
    return [
        PylonLvProfile(),
        JkPylonLvProfile(),
        JbdXiaoxiangProfile(),
        DalyUart485Profile(),
        JkRs485ModbusProfile(),
        PaceRs485ModbusV13Profile(),
        GrowattBmsRs4851xSxxpProfile(),
        VoltronicInverterBms485Profile(),
    ]


def get_research_profiles():
    return [WowRs485ModbusV13Profile()]


def get_profiles(include_unverified: bool = False):
    profiles = get_all_profiles()
    if include_unverified:
        profiles.extend(get_research_profiles())
    return profiles
