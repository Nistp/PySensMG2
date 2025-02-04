#!/usr/bin/env python3
"""Pymodbus Example which implements Reading from the SENS MicroGenius 2 Battery Charger Controller via RS485.

https://sens-usa.com/hubfs/SENS%20Custom%20Blog%20-%202024/Images/101324_MicroGenius2_User_Manual.pdf

Uses the contributed Solar.py example as a base for implementation.

"""
import logging
from enum import Enum
from math import log10
from time import sleep

from pymodbus import pymodbus_apply_logging_config

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus import FramerType


pymodbus_apply_logging_config(logging.ERROR)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
_logger = logging.getLogger(__file__)

# Define the client parameters here
PORT = "COM1"

def main() -> None:
    """Run client setup."""
    _logger.info("### Client starting")
    client: ModbusSerialClient = ModbusSerialClient(
        port=PORT,
        # Common optional parameters:
        framer=FramerType.SOCKET,
        timeout=5,
    )
    client.connect()
    _logger.info("### Client connected")
    sleep(1)
    _logger.info("### Client starting")
    for count in range(CYCLES):
        _logger.info(f"Running loop {count}")
        microgenius2_calls(client)
        sleep(10)  # scan interval
    client.close()
    _logger.info("### End of Program")


def microgenius2_calls(client: ModbusSerialClient) -> None:
    """Read registers."""
    error = False

    # Contains the Modbus Register Map for all of the Official Registers, i.e. Registers in the Manual
    # Some of the Register names combine the name with the description, since the names are sometime vague
    for addr, format, factor, comment, unit in ( # data_type according to ModbusClientMixin.DATATYPE.value[0]
        (0, "I", 1,     "System Serial Number",             "(Num)"),
        (2, "I", 1,     "Program Revision",                 "(Num)"),
        (4, "I", 1,     "Bootloader Version",               "(Num)"),
        (6, "I", 1,     "Device Type",                      "(Enum)"),
        (8, "i", 1,     "Serial Number",                    "(Num)"),
        (10, "H", 1,     "Build Date (year)",                "(Num)"),
        (11, "H", 1,     "Build Date (month and day)",       "(Num)"),
        (12, "I", 1,     "Model Number Characters 1-4",      "(Bit)"),
        (14, "I", 1,     "Model Number Characters 5-8",      "(Bit)"),
        (16, "I", 1,     "Model Number Characters 9-12",     "(Bit)"),
        (18, "I", 1,     "Model Number Characters 13-16",    "(Bit)"),
        (20, "I", 1,     "Model Number Characters 17-20",    "(Bit)"),
        (22, "I", 1,     "Model Number Characters 21-24",    "(Bit)"),
        (24, "I", 1,     "Model Number Characters 25-28",    "(Bit)"),
        (26, "I", 1,     "Model Number Characters 29-32",    "(Bit)"),
        (36, "I", 1,     "Number of Cranks Detected",        "(Num)"),
        (38, "I", 1,     "Number of Cranks Under Threshold", "(Num)"),
        (42, "I", 1,     "Basic Charging Alarms",            "(Bitfield)"),
        (44, "I", 1,     "Charging Status",                  "(Bitfield)"),
        (46, "I", 1,     "Charing Alarms Extended",          "(Bitfield)"),
        (48, "I", 1,     "Charging AC Alarms",               "(Bitfield)"),
        (62, "I", 1,     "Charger Uptime",                   "(Sec)"),
        (68, "I", 32768, "Default Output Batt Voltage",      "(Voltage)"),
        (70, "I", 32768, "Default Output Current",           "(Amperage)"),
        (72, "I", 32768, "Default Output Power",             "(Watts)"),
        (74, "I", 32768, "Default Output Float Setting",     "(V/Cell)"),
        (76, "I", 32768, "Default Output Boost Setting",     "(V/Cell)"),
        (78, "I", 32768, "Default Output Remote Temp",       "(Celsius)"),
        (80, "I", 32768, "Default Output Internal Temp",     "(Celsius)"),
        (82, "I", 1,     "Default Boost Elapsed Time",       "(Sec)"),
        (84,  "I", 1,     "Default Periodic Boost Countdown", "(Sec)"),
        (86,  "I", 10,    "Default Output AC LIne Frequency", "(Hz)"),
        (88,  "I", 32768, "Default AC Line Voltage 1",        "(Voltage)"),
        (90,  "I", 32768, "Default AC Line Current 1",        "(Amperage)"),
        (92,  "I", 32768, "Default AC Line Voltage 2",        "(Votlage)"),
        (94,  "I", 32768, "Default AC Line Current 2",        "(Amperage)"),
        (96,  "I", 32768, "Default AC Line Voltage 3",        "(Voltage)"),
        (98,  "I", 32768, "Default AC Line Current 3",        "(Amperage)"),
        (100, "I", 1,     "Battery Check Time Elapsed",       "(Sec)"),
        (102, "I", 1,     "Battery Check Due Time",           "(Sec)"),
        (104, "I", 1,     "Number of Chargers Detected",      "(Num"),
        (128, "I", 32768, "Default Output Max Power",         "(V/Cell)"), # Not sure why this is listed as V/cell in the manual if it's power
        (130, "I", 32768, "Default Output Max Voltage",       "(V/Cell)"),
        (132, "I", 32768, "Default Output Max Current",       "(Amperage)"),
        (134, "I", 32768, "Default Float Setting",            "(V/Cell)"),
        (136, "I", 32768, "Default Boost Setting",            "(V/Cell)"),
        (138, "I", 1,     "Default Program Mode",             "(Custom)"),
        (140, "I", 32768, "Default Program Cell Count",       "(Cells)"),
        (142, "I", 32768, "Default Temp Compensation Slope",  "(Celsius/Voltage"),
        (144, "I", 32768, "Low DC Alarm Setpoint",            "(V/Cell)"),
        (146, "I", 32768, "Low Crank Alarm Setpoint",         "(V/Cell)"),
        (148, "I", 32768, "Low Current Alarm Setpoint",       "(Amperage)"),
        (152, "I", 32768, "High DC Alarm Setpoint",           "(V/Cell)"),
        (154, "I", 32768, "OVSD Alarm Setpoint",              "(V/Cell)"),
        (156, "I", 32768, "Battery Discharge Alarm Setpoint", "(V/Cell)"),
        (158, "I", 32768, "End Discharge Alarm Setpoint",     "(V/Cell)"),
        (160, "I", 3600,  "Boost Time Limit",                 "(Hours)"),
        (162, "I", 32768, "Current Limit Setting",            "(% Rated Amperage"),
        (164, "I", 3600,  "Helix Float Time",                 "(Hours)"),
        (166, "I", 3600,  "Helix Refresh Time",               "(Hours)"),
        (168, "I", 3600,  "Helix Eco Time",                   "(Hours)"),
        (170, "I", 86400, "Interval between Periodic Boost",  "(Days)"),
        (172, "I", 32768, "Battery Check Voltage Setting",    "(V/Cell)"),
        (174, "I", 86400, "Default Battery Check Interval",   "(Days)"),
        (176,),
        (178,),
        (180,),
        (182,),
        (184,),
        (186,),
        (188,),
        (190,)
    ):
        if error:
            error = False
            client.close()
            sleep(0.1)
            client.connect()
            sleep(1)
        
        data_type = get_data_type(format)
        count = data_type.value[1]
        var_type = data_type.name

        _logger.info(f"*** Reading {comment} ({var_type})")
        
        try:
            rr = client.read_holding_registers(address=addr, count=count, slave=1)
        except ModbusException as exc:
            _logger.error(f"Modbus exception: {exc!s}")
            error = True
            continue
        if rr.isError():
            _logger.error(f"Error")
            error = True
            continue
        if isinstance(rr, ExceptionResponse):
            _logger.error(f"Response exception: {rr!s}")
            error = True
            continue
        
        value = client.convert_from_registers(rr.registers, data_type) / factor
        if factor < 1:
            value = round(value, int(log10(factor) * -1))
        _logger.info(f"*** READ *** {comment} = {value} {unit}")


def get_data_type(format: str) -> Enum:
    """Return the ModbusTcpClient.DATATYPE according to the format"""
    for data_type in ModbusSerialClient.DATATYPE:
        if data_type.value[0] == format:
            return data_type


if __name__ == "__main__":
    main()