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
HOST = ""
PORT = "COM1"

def main() -> None:
    """Run client setup."""
    _logger.info("### Client starting")
    client: ModbusSerialClient = ModbusSerialClient(
        host=HOST,
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
        (40001, "I", 1,     "System Serial Number",             "(Num)"),
        (40003, "I", 1,     "Program Revision",                 "(Num)"),
        (40005, "I", 1,     "Bootloader Version",               "(Num)"),
        (40007, "I", 1,     "Device Type",                      "(Enum)"),
        (40009, "i", 1,     "Serial Number",                    "(Num)"),
        (40011, "H", 1,     "Build Date (year)",                "(Num)"),
        (40012, "H", 1,     "Build Date (month and day)",       "(Num)"),
        (40013, "I", 1,     "Model Number Characters 1-4",      "(Bit)"),
        (40015, "I", 1,     "Model Number Characters 5-8",      "(Bit)"),
        (40017, "I", 1,     "Model Number Characters 9-12",     "(Bit)"),
        (40019, "I", 1,     "Model Number Characters 13-16",    "(Bit)"),
        (40021, "I", 1,     "Model Number Characters 17-20",    "(Bit)"),
        (40023, "I", 1,     "Model Number Characters 21-24",    "(Bit)"),
        (40025, "I", 1,     "Model Number Characters 25-28",    "(Bit)"),
        (40027, "I", 1,     "Model Number Characters 29-32",    "(Bit)"),
        (40037, "I", 1,     "Number of Cranks Detected",        "(Num)"),
        (40039, "I", 1,     "Number of Cranks Under Threshold", "(Num)"),
        (40043, "I", 1,     "Basic Charging Alarms",            "(Bitfield)"),
        (40045, "I", 1,     "Charging Status",                  "(Bitfield)"),
        (40047, "I", 1,     "Charing Alarms Extended",          "(Bitfield)"),
        (40049, "I", 1,     "Charging AC Alarms",               "(Bitfield)"),
        (40063, "I", 1,     "Charger Uptime",                   "(Sec)"),
        (40069, "I", 32768, "Default Output Batt Voltage",      "(Voltage)"),
        (40071, "I", 32768, "Default Output Current",           "(Amperage)"),
        (40073, "I", 32768, "Default Output Power",             "(Watts)"),
        (40075, "I", 32768, "Default Output Float Setting",     "(V/Cell)"),
        (40077, "I", 32768, "Default Output Boost Setting",     "(V/Cell)"),
        (40079, "I", 32768, "Default Output Remote Temp",       "(Celsius)"),
        (40081, "I", 32768, "Default Output Internal Temp",     "(Celsius)"),
        (40083, "I", 1,     "Default Boost Elapsed Time",       "(Sec)"),
        (40085, "I", 1,     "Default Periodic Boost Countdown", "(Sec)"),
        (40087, "I", 10,    "Default Output AC LIne Frequency", "(Hz)"),
        (40089, "I", 32768, "Default AC Line Voltage 1",        "(Voltage)"),
        (40091, "I", 32768, "Default AC Line Current 1",        "(Amperage)"),
        (40093, "I", 32768, "Default AC Line Voltage 2",        "(Votlage)"),
        (40095, "I", 32768, "Default AC Line Current 2",        "(Amperage)"),
        (40097, "I"< 32768, "Default AC Line Voltage 3",        "(Voltage)"),
        (40099, "I", 32768, "Default AC Line Current 3",        "(Amperage)"),
        (40101, "I", 1,     "Battery Check Time Elapsed",       "(Sec)"),
        (40103, "I", 1,     "Battery Check Due Time",           "(Sec)"),
        (40105, "I", 1,     "Number of Chargers Detected",      "(Num"),
        (40129, "I", 32768, "Default Output Max Power",         "(V/Cell)"), # Not sure why this is listed as V/cell in the manual if it's power
        (40131, "I", 32768, "Default Output Max Voltage",       "(V/Cell)"),
        (40133, "I", 32768, "Default Output Max Current",       "(Amperage)"),
        (40135, "I", 32768, "Default Float Setting",            "(V/Cell)"),
        (40137, "I", 32768, "Default Boost Setting",            "(V/Cell)"),
        (40139, "I", 1,     "Default Program Mode",             "(Custom)"),
        (40141, "I", 32768, "Default Program Cell Count",       "(Cells)"),
        (40143, "I", 32768, "Default Temp Compensation Slope",  "(Celsius/Voltage"),
        (40145, "I", 32768, "Low DC Alarm Setpoint",            "(V/Cell)"),
        (40147, "I", 32768, "Low Crank Alarm Setpoint",         "(V/Cell)"),
        (40149, "I", 32768, "Low Current Alarm Setpoint",       "(Amperage)"),
        (40153, "I", 32768, "High DC Alarm Setpoint",           "(V/Cell)"),
        (40155, "I", 32768, "OVSD Alarm Setpoint",              "(V/Cell)"),
        (40157, "I", 32768, "Battery Discharge Alarm Setpoint", "(V/Cell)"),
        (40159, "I", 32768, "End Discharge Alarm Setpoint",     "(V/Cell)"),
        (40161, "I", 3600,  "Boost Time Limit",                 "(Hours)"),
        (40163, "I", 32768, "Current Limit Setting",            "(% Rated Amperage"),
        (40165, "I", 3600,  "Helix Float Time",                 "(Hours)"),
        (40167, "I", 3600,  "Helix Refresh Time",               "(Hours)"),
        (40169, "I", 3600,  "Helix Eco Time",                   "(Hours)"),
        (40171, "I", 86400, "Interval between Periodic Boost",  "(Days)"),
        (40173, "I", 32768, "Battery Check Voltage Setting",    "(V/Cell)"),
        (40175, "I", 86400, "Default Battery Check Interval",   "(Days)"),
        (40177,),
        (40179,),
        (40181,),
        (40183,),
        (40185,),
        (40187,),
        (40189,),
        (40191,)
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
        
        value = client.convert_from_registers(rr.registers, data_type) * factor
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