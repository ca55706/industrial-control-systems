#!/usr/bin/env python3

import socket

# Simulated PLC holding registers
# Register 0 = Sensor Value
# Register 1 = Motor State
registers = [0] * 10

HOST = "127.0.0.1"
PORT = 1502

print("PLC register service running on port 1502")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)

while True:
    conn, addr = server.accept()

    try:
        data = conn.recv(1024).decode().strip().split()

        if not data:
            conn.close()
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

            if 0 <= reg < len(registers):
                registers[reg] = value

                # PLC control logic
                # Sensor > 50 turns the motor ON
                if reg == 0:
                    if registers[0] > 50:
                        registers[1] = 1
                    else:
                        registers[1] = 0

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
