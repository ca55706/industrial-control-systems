#!/usr/bin/env python3

import asyncio

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusDeviceContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer


HOST = "127.0.0.1"
PORT = 1502


# --------------------------------------------------
# PLC HOLDING REGISTERS
# --------------------------------------------------
#
# Register 0 = Tank Level
# Register 1 = Temperature
# Register 2 = Safety Interlock
# Register 3 = Pump State
#
# Initial values:
#
# Tank Level       = 20
# Temperature      = 85
# Safety Interlock = 0
# Pump State       = 0
#

holding_registers = ModbusSequentialDataBlock(
    0,
    [20, 85, 0, 0] + [0] * 96
)

device = ModbusDeviceContext(
    hr=holding_registers
)

context = ModbusServerContext(
    devices=device,
    single=True
)

flag_printed = False


# --------------------------------------------------
# PLC CONTROL LOGIC
# --------------------------------------------------

async def plc_logic():

    global flag_printed

    while True:

        # Function code 3 = Holding Registers
        values = device.getValues(
            3,
            0,
            count=4
        )

        tank_level = values[0]
        temperature = values[1]
        safety = values[2]

        # Required safety conditions:
        #
        # Tank Level:       60 - 90
        # Temperature:      below 70
        # Safety Interlock: ON (1)

        if (
            60 <= tank_level <= 90
            and temperature < 70
            and safety == 1
        ):

            # Turn pump ON
            device.setValues(
                3,
                3,
                [1]
            )

            if not flag_printed:

                print()
                print("========================================")
                print("PUMP ACTIVATED")
                print("Safety conditions satisfied.")
                print("Challenge complete!")
                print("========================================")

                try:

                    with open("/flag", "r") as f:
                        flag = f.read().strip()

                    print("FLAG:")
                    print(flag)

                except PermissionError:

                    print(
                        "FLAG ERROR: "
                        "/flag permission denied"
                    )

                except FileNotFoundError:

                    print(
                        "FLAG ERROR: "
                        "/flag does not exist"
                    )

                flag_printed = True

        else:

            # Conditions are not satisfied.
            # Keep the pump OFF.

            device.setValues(
                3,
                3,
                [0]
            )

        await asyncio.sleep(0.25)


# --------------------------------------------------
# MODBUS TCP SERVER
# --------------------------------------------------

async def main():

    print(
        f"Modbus TCP server listening "
        f"on {HOST}:{PORT}"
    )

    print()
    print("Holding Registers:")
    print("HR0 = Tank Level")
    print("HR1 = Temperature")
    print("HR2 = Safety Interlock")
    print("HR3 = Pump State")
    print()

    logic_task = asyncio.create_task(
        plc_logic()
    )

    try:

        await StartAsyncTcpServer(
            context=context,
            address=(HOST, PORT)
        )

    finally:

        logic_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
