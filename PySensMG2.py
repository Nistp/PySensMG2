#!/usr/bin/env python3
"""Pymodbus Example which implements Reading from the SENS MicroGenius 2 Battery Charger Controller.

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
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus import FramerType


'''
HOST = "modbusServer.lan"
PORT = 502
CYCLES = 4
'''


pymodbus_apply_logging_config(logging.ERROR)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
_logger = logging.getLogger(__file__)


def main() -> None:
    """Run client setup."""
    _logger.info("### Client starting")
    client: ModbusTcpClient = ModbusTcpClient(
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
        solar_calls(client)
        sleep(10)  # scan interval
    client.close()
    _logger.info("### End of Program")


def solar_calls(client: ModbusTcpClient) -> None:
    """Read registers."""
    error = False
        
    for addr, format, factor, comment, unit in ( # data_type according to ModbusClientMixin.DATATYPE.value[0]
        (40001, "H", 1,     "System Serial Number (low)",       "(Num)"),
        (40002, "H", 1,     "System Serial Number (high)",      "(Num)"),
        (40003, "H", 1,     "Program Revision (low)",           "(Num)"),
        (40004, "H", 1,     "Program Revision (high)",          "(Num)"),
        (40005, "H", 1,     "Bootloader Version (low)",         "(Num)"),
        (40006, "H", 1,     "Device Type (low)",                "(Enum)"),
        (40007, "H", 1,     "Device Type (high)",               "(Enum)"),
        (40008, "i", 1,     "Serial Number (low)",              "(Num)"),
        (40009, "i", 1,     "Serial Number (high)",             "(Num)"),
        (40010, "i", 1,     "Build Date (year)",                "(Num)"),
        (40011, "I", 1,     "Build Date (month and day)",       "(Num)"),
        (40012)
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
    for data_type in ModbusTcpClient.DATATYPE:
        if data_type.value[0] == format:
            return data_type


if __name__ == "__main__":
    main()