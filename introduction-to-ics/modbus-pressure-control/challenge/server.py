#!/usr/bin/env python3

import asyncio
from pathlib import Path

from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import SimData, SimDevice, DataType

HOST = "127.0.0.1"
PORT = 1502

# HR0 = Pressure (initially 40)
# HR1 = Pump State (initially 0)
device = SimDevice(
    1,
    SimData(
        0,
        values=[40, 0],
        datatype=DataType.REGISTERS
    )
)

server = ModbusTcpServer(
    device,
    address=(HOST, PORT)
)

async def pump_logic():
    flag_awarded = False

    while True:
        values = await server.async_getValues(
            1, 3, 0, count=1
        )

        pressure = values[0]
        pump_state = 1 if pressure > 80 else 0

        # Update HR1
        await server.async_setValues(
            1, 3, 1, [pump_state]
        )

        if pump_state == 1 and not flag_awarded:
            flag = Path("/flag").read_bytes()
            reward = Path("/home/hacker/pump-flag")
            reward.write_bytes(flag)
            reward.chmod(0o644)
            flag_awarded = True

        await asyncio.sleep(0.5)

async def main():
    asyncio.create_task(pump_logic())
    await server.serve_forever()

asyncio.run(main())
