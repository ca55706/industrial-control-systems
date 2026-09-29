#!/usr/bin/env python3

import socket

# PLC Holding Registers
# Register 0 = Pressure
# Register 1 = Temperature
# Register 2 = Safety Switch
# Register 3 = Pump State

registers = [0, 100, 0, 0]

HOST = "127.0.0.1"
PORT = 1502


def evaluate_logic():
    pressure = registers[0]
    temperature = registers[1]
    safety = registers[2]

    # PLC safety interlock logic
    if 40 <= pressure <= 80 and temperature < 70 and safety == 1:
        registers[3] = 1
    else:
        registers[3] = 0


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen(5)

print("PLC Safety Interlock service running on port 1502")

while True:
    conn, addr = server.accept()

    try:
        data = conn.recv(1024).decode().strip().split()

        if not data:
            continue

        command = data[0].upper()

        # READ <register>
        if command == "READ" and len(data) == 2:
            reg = int(data[1])

            if 0 <= reg < len(registers):
                response = str(registers[reg])
            else:
                response = "INVALID REGISTER"

        # WRITE <register> <value>
        elif command == "WRITE" and len(data) == 3:
            reg = int(data[1])
            value = int(data[2])

            # Pump output cannot be directly modified
            if reg == 3:
                response = "ACCESS DENIED"

            elif 0 <= reg <= 2:
                registers[reg] = value
                evaluate_logic()
                response = "OK"

            else:
                response = "INVALID REGISTER"

        else:
            response = "ERROR"

        conn.sendall((response + "\n").encode())

    except Exception:
        conn.sendall(b"ERROR\n")

    finally:
        conn.close()
