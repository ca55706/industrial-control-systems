#!/usr/bin/env python3

import asyncio
import sys

sys.path.insert(0, "/challenge/challenge/pymodbus.zip")

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
# Note:
# This pymodbus version internally adjusts the
# datastore address by -1, so the data block starts
# at address 1.
#

holding_registers = ModbusSequentialDataBlock(
    1,
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

        # Read the four holding registers.
        #
        # Internal address 1 = HR0 Tank Level
        # Internal address 2 = HR1 Temperature
        # Internal address 3 = HR2 Safety Interlock
        # Internal address 4 = HR3 Pump State

        values = holding_registers.getValues(
            1,
            count=4
        )

        tank_level = values[0]
        temperature = values[1]
        safety = values[2]

        # --------------------------------------------------
        # PUMP SAFETY CONDITIONS
        # --------------------------------------------------
        #
        # Tank Level:       60 - 90
        # Temperature:      below 70
        # Safety Interlock: ON (1)
        #

        if (
            60 <= tank_level <= 90
            and temperature < 70
            and safety == 1
        ):

            # All safety conditions are satisfied.
            # Turn the pump ON.
            #
            # Internal address 4 corresponds to HR3.

            holding_registers.setValues(
                4,
                [1]
            )

            # Print the flag only once.

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

            # One or more safety conditions are not
            # satisfied. Keep the pump OFF.

            holding_registers.setValues(
                4,
                [0]
            )

        # Check PLC conditions four times per second.
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

    # Run the PLC control logic in the background.
    logic_task = asyncio.create_task(
        plc_logic()
    )

    try:

        # Start the Modbus TCP server.
        await StartAsyncTcpServer(
            context=context,
            address=(HOST, PORT)
        )

    finally:

        # Stop the PLC logic task when the server exits.
        logic_task.cancel()


# --------------------------------------------------
# PROGRAM ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
