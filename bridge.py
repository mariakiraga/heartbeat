import serial
import socket

SERIAL_PORT = "COM3"
BAUD_RATE = 115200
UNITY_IP = "127.0.0.1"
UNITY_PORT = 5005
UI_IP      = "127.0.0.1"
UI_PORT    = 5006

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Bridge running: {SERIAL_PORT} @ {BAUD_RATE} baud")
print(f"  → Unity  UDP {UNITY_IP}:{UNITY_PORT}")
print(f"  → UI     UDP {UI_IP}:{UI_PORT}")

while True:
    line = ser.readline().decode("utf-8").strip()
    if "BEAT" in line:
        sock.sendto(line.encode("utf-8"), (UNITY_IP, UNITY_PORT))
        sock.sendto(line.encode("utf-8"), (UI_IP, UI_PORT))
        print(line)