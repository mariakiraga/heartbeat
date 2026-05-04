# Haptic Heartbeat Monitor

This project captures real-time pulse data from a KY-039 analog sensor, relays it via a Python bridge, and maps the heartbeat to both a bHaptics X40 vest (via Unity) and a graphical dashboard for monitoring and guided breathing exercises. The system translates physical biological signals into immediate haptic and visual feedback.

## Research context

---

## Prerequisites 
### Hardware:
- bHaptics TactSuit X40 vest
- Arduino microcontroller
- KY-039 analog pulse sensor

### Software:
- bHaptics Player
- Unity Editor (with bHaptics SDK2 installed, you can follow guide on [bHaptics site](https://docs.bhaptics.com/sdk/unity/guide/))
- Arduino IDE
- Python 3.x

### Python Dependencies:
- pyserial
- PyQt6
- pyqtgraph
- numpy

## Project Structure

## Installation
1. Connect the KY-039 sensor to the Arduino. Ensure the signal pin is connected to analog pin A0.
2. Set up your Python virtual environment and install the required packages:
```bash
pip install pyserial PyQt6 pyqtgraph numpy
```
4. Open the Unity project. Ensure the bHaptics SDK is imported. Attach the `HeartbeatReceiver` script to the `HapticManager` object in your active scene.
5. Verify the serial port configuration. The Arduino sketch operates at a baud rate of 115200. The `bridge.py` script is hardcoded to `COM3`. Update the `SERIAL_PORT` variable in `bridge.py` if your Arduino mounts to a different port.

---

## Running the system
The startup sequence is critical. The physical and receiving layers must be active before the transmitting scripts are executed.

### Step 1: Hardware and bHaptics Player
- Power on the bHaptics X40 vest.
- Launch the bHaptics Player application on your computer to establish the baseline hardware connection.

### Step 2: Unity
- Open the Unity project and load the scene containing the [bHaptics] objects and the `HapticManager` with the `HeartbeatReceiver` script.
- Press Play in the Unity Editor.
- Verify the connection by checking the Unity Console. You must see the message: `HeartbeatReceiver listening on UDP port 5005`. This confirms the server is waiting for data.

### Step 3: Arduino
- Open the Arduino IDE and upload the pulse detection sketch to the board.
- Make sure to slose the Arduino Serial Monitor after uploading to free the COM port for the Python script.

### Step 4: Python Bridge
- Open a terminal and activate your Python environment.
- Navigate to the directory containing `bridge.py`.
- Execute the script:
```bash
python bridge.py
```
- This script reads the pulse from the COM port and forwards the impulses to Unity (port 5005) and the UI (port 5006).

### Step 5: Visualisation UI
- Open a separate terminal window (or tab) within the same Python environment.
- Execute the dashboard script:
```bash
python ui.py
```
- The application will launch, displaying the real-time heartbeat visualisation and the breathing technique interface.

---

<img width="966" height="594" alt="viz" src="https://github.com/user-attachments/assets/0371a6c8-b810-4e75-9249-3032ff9f0695" />



