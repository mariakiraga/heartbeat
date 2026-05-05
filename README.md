# Haptic Heartbeat Monitor

This project captures real-time pulse data from a KY-039 analog sensor, relays it via a Python bridge, and maps each heartbeat to both a bHaptics X40 haptic vest (via Unity) and a graphical dashboard for real-time monitoring. The system translates a raw biological signal into immediate haptic and visual feedback.

## Research context

The project is grounded in research on **interoception** — the ability to consciously perceive and interpret signals originating from within the body, such as heartbeat and breath. Interoceptive awareness is linked to emotion regulation, and its disruption is associated with difficulties in managing affective states.

Tactile and vibratory stimulation are considered among the most direct channels for influencing the nervous system. Research on haptic biofeedback devices (e.g., *doppel*, *ambienBeat*) has demonstrated that vibrotactile stimuli that mirror heartbeat rhythms can facilitate physiological synchronisation and reduce anxiety without significant cognitive load.

This system provides **veridical haptic biofeedback** — the vest reproduces the user's own pulse in real time. The modular architecture is intentionally designed to allow future experiments in which the transmitted heartbeat rate is modified independently of the real one, enabling investigation of how altered interoceptive signals affect arousal and emotional states.

---

## Prerequisites

### Hardware
- bHaptics TactSuit X40 vest
- Arduino microcontroller (Uno or compatible)
- KY-039 analog pulse sensor

### Software
- [bHaptics Player](https://www.bhaptics.com/support/player) — must be running before Unity
- Unity Editor with bHaptics SDK2 installed ([setup guide](https://docs.bhaptics.com/sdk/unity/guide/))
- Arduino IDE
- Python 3.x

### Python dependencies
```bash
pip install pyserial PyQt6 pyqtgraph numpy
```

---

## Project structure

```
haptic-heartbeat-monitor/
├── pulse_monitor.ino        # Arduino sketch: DSP signal processing, beat detection
├── bridge.py                # Python bridge: Serial → UDP (Unity port 5005, UI port 5006)
├── ui.py                    # PyQt6 monitoring dashboard: waveform, BPM, HRV
└── HeartbeatReceiver.cs     # Unity C# script: UDP listener + bHaptics vest control
```

| File | Role |
|------|------|
| `pulse_monitor.ino` | Reads KY-039 on pin A0, applies 20 ms averaging windows and 4-sample rolling average, detects rising edge, sends `"BEAT"` over Serial at 115 200 baud |
| `bridge.py` | Reads `"BEAT"` flags from the COM port; retransmits to Unity (UDP 5005) and the UI (UDP 5006). The only layer with COM port access |
| `ui.py` | PyQt6 + pyqtgraph dashboard: pulsing heart orb, scrolling PPG waveform, rolling BPM, HRV (SDNN). Listens on UDP 5006 |
| `HeartbeatReceiver.cs` | Background-thread UDP listener in Unity; triggers `BhapticsLibrary.PlayMotors()` with a spatial 40-motor gradient pattern on each beat |

---

## Installation

1. **Wire the sensor.** Connect the KY-039 signal pin to analog pin **A0** on the Arduino. Connect VCC to 5 V and GND to GND.

2. **Upload the Arduino sketch.** Open `pulse_monitor.ino` in the Arduino IDE and upload it to the board.

3. **Install Python dependencies.**
```bash
pip install pyserial PyQt6 pyqtgraph numpy
```

4. **Configure the serial port.** Open `bridge.py` and set `SERIAL_PORT` to match the port your Arduino mounts on:
   - Windows: typically `"COM3"` or `"COM4"` (check Device Manager)
   - Linux/macOS: typically `"/dev/ttyUSB0"` or `"/dev/tty.usbmodem*"`

5. **Set up Unity.** Open the Unity project, import the bHaptics SDK2 package, and attach `HeartbeatReceiver.cs` to a `HapticManager` GameObject in your active scene.

---

## Running the system

The startup sequence is critical — receiving layers must be active before the transmitting bridge is started.

### Step 1 — Hardware and bHaptics Player
- Power on the bHaptics X40 vest and ensure it is paired via Bluetooth.
- Launch **bHaptics Player** on your computer to establish the baseline hardware connection. Keep it running in the background.

### Step 2 — Unity
- Open the Unity project and load the scene containing the `HapticManager` with `HeartbeatReceiver`.
- Press **Play** in the Unity Editor.
- Confirm in the Unity Console:
```
HeartbeatReceiver listening on UDP port 5005
```
This confirms Unity is ready to receive beat events.

### Step 3 — Arduino
- Upload `pulse_monitor.ino` via the Arduino IDE if not already done.
- **Close the Serial Monitor** after uploading — leaving it open will lock the COM port and prevent `bridge.py` from connecting.

### Step 4 — Python bridge
Open a terminal and run:
```bash
python bridge.py
```
The bridge connects to the COM port and begins forwarding `BEAT` packets to both Unity (5005) and the UI (5006). Expected output:
```
Bridge running: COM3 @ 115200 baud
  → Unity  UDP 127.0.0.1:5005
  → UI     UDP 127.0.0.1:5006
BEAT
BEAT
...
```

### Step 5 — Monitoring dashboard
Open a second terminal and run:
```bash
python ui.py
```
The dashboard will launch and begin displaying the live heartbeat visualisation.

---

## Dashboard

The UI displays:
- **Heart orb** — pulses on each detected beat
- **PPG waveform** — scrolling real-time signal
- **BPM** — rolling average over the last 8 RR intervals (physiologically correct: RR intervals are averaged first, then converted to BPM)
- **HRV** — SDNN of the last 8 RR intervals in milliseconds; a key interoceptive indicator (low values suggest stress-driven rigidity; higher values indicate parasympathetic tone)
- **Beat count** — total beats since session start

Use the **pause** button to freeze the display without stopping the bridge or Unity. The **☀ / ☾** button toggles between dark and light themes.

---

## Tuning

If beat detection is unreliable, adjust these constants in `pulse_monitor.ino`:

| Constant | Default | Effect |
|----------|---------|--------|
| `RISE_THRESHOLD` | `4` | Consecutive rising windows required to confirm a beat. Lower = more sensitive (more false positives); higher = more robust (may miss weak beats) |
| `ROLLING_AVG_SIZE` | `4` | Samples in the rolling average. Higher = smoother signal, slower response |
| `SAMPLE_WINDOW_MS` | `20` | Averaging window duration. Keep at 20 ms to cancel 50 Hz mains noise |

If BPM is unstable, adjust `WINDOW` in `ui.py` (default `8`). A larger window produces a more stable reading at the cost of slower response to genuine heart rate changes.

---

<img width="966" height="594" alt="viz" src="https://github.com/user-attachments/assets/0371a6c8-b810-4e75-9249-3032ff9f0695" />
