import serial
import socket

SERIAL_PORT = "COM3"
BAUD_RATE = 115200
UNITY_IP = "127.0.0.1"
UNITY_PORT = 5005

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Bridging {SERIAL_PORT} -> UDP {UNITY_IP}:{UNITY_PORT}")

while True:
    line = ser.readline().decode("utf-8").strip()
    if "BEAT" in line:
        sock.sendto(line.encode("utf-8"), (UNITY_IP, UNITY_PORT))
        print(line)