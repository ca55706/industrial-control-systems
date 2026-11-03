
#!/usr/bin/env python3

import asyncio
from pathlib import Path

from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import SimData, SimDevice, DataType

# -------------------------------------------
# MODBUS TCP CONFIGURATION
# -------------------------------------------

HOST = "127.0.0.1"
PORT = 1502
DEVICE_ID = 1

# -------------------------------------------
# PLC HOLDING REGISTERS
# -------------------------------------------
#
# HR0 = Pressure
# HR1 = Pump State
#
# Initial values:
# Pressure   = 40
# Pump State = 0 (OFF)
#
# Pump activates when pressure > 80
# -------------------------------------------

device = SimDevice(
    DEVICE_ID,
    SimData(
        0,
        values=[40, 0],
        datatype=DataType.REGISTERS
    )
)

# -------------------------------------------
# FLAG CONFIGURATION
# -------------------------------------------

FLAG_PATH = Path("/flag")
REWARD_DIR = Path("/run/pump-challenge")
REWARD_PATH = REWARD_DIR / "flag"

# -------------------------------------------
# PLC CONTROL LOGIC
# -------------------------------------------

async def pump_logic(server):

    flag_awarded = False

    while True:

        # Read pressure from HR0
        values = await server.async_getValues(
            DEVICE_ID,
            3,
            0,
            count=1
        )

        pressure = values[0]

        # Determine pump state
        if pressure > 80:
            pump_state = 1
        else:
            pump_state = 0

        # Update HR1 (Pump State)
        await server.async_setValues(
            DEVICE_ID,
            3,
            1,
            [pump_state]
        )

        # Award flag once pump is activated
        if pump_state == 1 and not flag_awarded:

            REWARD_DIR.mkdir(
                mode=0o755,
                parents=True,
                exist_ok=True
            )

            REWARD_DIR.chmod(0o755)

            flag = FLAG_PATH.read_bytes()

            REWARD_PATH.write_bytes(flag)
            REWARD_PATH.chmod(0o644)

            flag_awarded = True

            print(
                "Pump activated! Flag awarded.",
                flush=True
            )

        await asyncio.sleep(0.5)

# -------------------------------------------
# START MODBUS TCP SERVER
# -------------------------------------------

async def main():

    server = ModbusTcpServer(
        device,
        address=(HOST, PORT)
    )

    print(
        f"Modbus TCP server running on {HOST}:{PORT}",
        flush=True
    )

    print(
        "HR0 = Pressure (40)",
        flush=True
    )

    print(
        "HR1 = Pump State (0)",
        flush=True
    )

    print(
        "Objective: Set pressure above 80",
        flush=True
    )

    asyncio.create_task(pump_logic(server))

    await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
