"""
ui.py  —  Pulse Monitor (interoception)
Listens for BEAT on UDP 5006 (sent by bridge.py).

Displays:
  · Pulsing heart orb
  · Rolling waveform
  · BPM  — 8-beat rolling average (stable)
  · HRV  — std dev of last 8 RR intervals in ms (interoceptive signal)
  · Beat count

Dependencies:
    pip install PyQt6 pyqtgraph numpy
"""

import sys, socket, time, math
import numpy as np
import pyqtgraph as pg

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath

# ── Palette ───────────────────────────────────────────────────────────────────

DARK = {
    "bg":     "#12121A", "panel":  "#1C1C28",
    "border": "#2C2C3C", "sage":   "#7a9e8e",
    "sage_d": "#1e2e28", "rose":   "#c4847a",
    "rose_d": "#2e1e1c", "cream":  "#d8d4cc",
    "muted":  "#555552", "faint":  "#222222",
    "wave":   "#c4847a",
}
LIGHT = {
    "bg":     "#F2EFE9", "panel":  "#FFFFFF",
    "border": "#E0DAD0", "sage":   "#5a8070",
    "sage_d": "#e4f0ea", "rose":   "#b06a60",
    "rose_d": "#f5e0dc", "cream":  "#282420",
    "muted":  "#999990", "faint":  "#ece8e0",
    "wave":   "#b06a60",
}

# Number of beats used for rolling BPM and HRV
WINDOW = 8


# ── Heart orb ─────────────────────────────────────────────────────────────────

class HeartOrb(QWidget):
    SIZE = 80

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self._scale    = 1.0
        self._active   = False
        self._beat_col = QColor("#c4847a")
        self._rest_col = QColor("#2e1e1c")
        t = QTimer(self); t.setInterval(16); t.timeout.connect(self._step); t.start()

    def beat(self):
        self._scale = 1.20; self._active = True

    def set_palette(self, beat: str, rest: str):
        self._beat_col = QColor(beat)
        self._rest_col = QColor(rest)
        self.update()

    def _step(self):
        if self._scale > 1.002:
            self._scale += (1.0 - self._scale) * 0.16
            self.update()
        elif self._active:
            self._active = False
            self._scale  = 1.0

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, s = self.width() / 2, self.height() / 2, self._scale
        # Background circle
        r = 36 * s
        p.setPen(QPen(self._beat_col, 1.0))
        p.setBrush(QBrush(self._beat_col if self._active else self._rest_col))
        p.drawEllipse(QPointF(cx, cy), r, r)
        # Parametric heart
        path = QPainterPath()
        pts  = []
        for i in range(100):
            t  = 2 * math.pi * i / 99
            hx = 16 * math.sin(t) ** 3
            hy = -(13*math.cos(t) - 5*math.cos(2*t)
                   - 2*math.cos(3*t) - math.cos(4*t))
            pts.append((cx + hx * 1.2 * s, cy + hy * 1.2 * s))
        path.moveTo(*pts[0])
        for px, py in pts[1:]:
            path.lineTo(px, py)
        path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._beat_col))
        p.drawPath(path)


# ── Helpers ───────────────────────────────────────────────────────────────────

def hline():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setObjectName("sep")
    return f


# ── Main window ───────────────────────────────────────────────────────────────

class PulseDashboard(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("pulse monitor")
        self.setFixedSize(720, 420)

        self._theme   = DARK
        self._is_dark = True
        self._paused  = False

        # Beat tracking
        self._beat_count   = 0
        self._last_beat_ts = None
        self._rr_intervals = []   # last WINDOW RR intervals in ms

        # Waveform ring buffer
        self._buf  = 400
        self._wavy = np.zeros(self._buf)
        self._wavx = np.arange(self._buf)

        # UDP — non-blocking drain pattern
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("127.0.0.1", 5006))
        self._sock.setblocking(False)

        self._build_ui()
        self._apply_theme()

        self._timer = QTimer(self)
        self._timer.setInterval(20)   # 50 fps
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root  = QWidget(); self.setCentralWidget(root)
        vroot = QVBoxLayout(root)
        vroot.setContentsMargins(16, 14, 16, 14)
        vroot.setSpacing(10)

        # Toolbar
        tb = QHBoxLayout(); tb.setSpacing(8)

        self._lbl_title = QLabel("pulse monitor")
        self._lbl_title.setObjectName("title")
        tb.addWidget(self._lbl_title)
        tb.addStretch()

        self._btn_pause = QPushButton("pause")
        self._btn_pause.setObjectName("smallBtn")
        self._btn_pause.setCheckable(True)
        self._btn_pause.clicked.connect(self._toggle_pause)
        tb.addWidget(self._btn_pause)

        self._btn_theme = QPushButton("☀")
        self._btn_theme.setObjectName("smallBtn")
        self._btn_theme.setFixedWidth(34)
        self._btn_theme.clicked.connect(self._toggle_theme)
        tb.addWidget(self._btn_theme)

        vroot.addLayout(tb)
        vroot.addWidget(hline())

        # Main row: left panel + waveform
        main = QHBoxLayout(); main.setSpacing(16); main.setContentsMargins(0, 0, 0, 0)

        # Left: orb + stats card
        left = QVBoxLayout(); left.setSpacing(12)
        left.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._heart = HeartOrb()
        left.addWidget(self._heart, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Stats card
        card = QFrame(); card.setObjectName("card")
        cf   = QVBoxLayout(card)
        cf.setContentsMargins(14, 10, 14, 10); cf.setSpacing(5)

        self._row_bpm   = self._stat_row("bpm",       "--")
        self._row_hrv   = self._stat_row("hrv (ms)",  "--")
        self._row_beats = self._stat_row("beats",      "0")

        for row in (self._row_bpm, self._row_hrv, self._row_beats):
            cf.addLayout(row)

        # # HRV tooltip hint
        # hrv_hint = QLabel("std dev of last 8 RR intervals")
        # hrv_hint.setObjectName("hint")
        # cf.addWidget(hrv_hint)

        left.addWidget(card)
        left.addStretch()
        main.addLayout(left)

        # Waveform
        self._wplot = pg.PlotWidget()
        self._wplot.setYRange(-1.4, 1.4)
        self._wplot.getPlotItem().hideAxis("bottom")
        self._wplot.getPlotItem().hideAxis("left")
        self._wplot.showGrid(x=False, y=False)
        self._wline = self._wplot.plot(self._wavx, self._wavy)
        main.addWidget(self._wplot, stretch=1)

        vroot.addLayout(main, stretch=1)

    def _stat_row(self, label, val):
        row = QHBoxLayout(); row.setSpacing(6)
        lbl     = QLabel(label); lbl.setObjectName("micro")
        val_lbl = QLabel(val);   val_lbl.setObjectName("statVal")
        val_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(lbl); row.addStretch(); row.addWidget(val_lbl)
        row._val = val_lbl   # handy reference for updates
        return row

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {t['bg']}; color: {t['cream']};
            }}
            #card {{
                background-color: {t['panel']};
                border: 1px solid {t['border']};
                border-radius: 10px;
            }}
            #sep   {{ color: {t['border']}; }}
            #title {{
                font-family: Georgia; font-size: 15px; color: {t['cream']};
            }}
            #statVal {{
                font-family: Georgia; font-size: 13px; color: {t['cream']};
            }}
            #micro {{
                font-family: Helvetica; font-size: 10px; color: {t['muted']};
            }}
            #hint {{
                font-family: Helvetica; font-size: 9px;
                color: {t['muted']}; font-style: italic;
            }}
            QPushButton {{
                background-color: {t['panel']}; color: {t['cream']};
                border: 1px solid {t['border']}; border-radius: 7px;
                padding: 5px 12px; font-size: 11px; font-family: Helvetica;
            }}
            QPushButton:hover {{
                background-color: {t['sage_d']}; color: {t['sage']};
                border-color: {t['sage']};
            }}
            QPushButton:checked {{
                background-color: {t['rose_d']}; color: {t['rose']};
                border-color: {t['rose']};
            }}
            #smallBtn {{ padding: 4px 10px; }}
        """)
        self._wplot.setBackground(t["bg"])
        self._wline.setPen(pg.mkPen(color=t["wave"], width=1.5))
        self._heart.set_palette(t["rose"], t["rose_d"])

    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        self._theme   = DARK if self._is_dark else LIGHT
        self._btn_theme.setText("☀" if self._is_dark else "☾")
        self._apply_theme()

    # ── Controls ──────────────────────────────────────────────────────────────

    def _toggle_pause(self):
        self._paused = self._btn_pause.isChecked()
        self._btn_pause.setText("resume" if self._paused else "pause")

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick(self):
        # Non-blocking UDP drain
        beat = False
        try:
            while True:
                data, _ = self._sock.recvfrom(1024)
                if data.decode("utf-8", errors="ignore").strip() == "BEAT":
                    beat = True
        except BlockingIOError:
            pass

        if self._paused:
            return

        if beat:
            self._on_beat()

        # Scroll waveform — near-zero noise baseline, sharp spike on beat
        self._wavy = np.roll(self._wavy, -1)
        self._wavy[-1] = 0.80 if beat else np.random.uniform(-0.04, 0.04)
        self._wline.setData(self._wavx, self._wavy)
        if beat:
            QTimer.singleShot(50,  lambda: self._push_wave(-0.65))
            QTimer.singleShot(100, lambda: self._push_wave(0.0))

    def _push_wave(self, val):
        self._wavy = np.roll(self._wavy, -1)
        self._wavy[-1] = val
        self._wline.setData(self._wavx, self._wavy)

    # ── Beat processing ───────────────────────────────────────────────────────

    def _on_beat(self):
        now = time.time()
        self._beat_count += 1
        self._heart.beat()

        if self._last_beat_ts is not None:
            rr_ms = (now - self._last_beat_ts) * 1000.0
            self._rr_intervals.append(rr_ms)
            # Keep a rolling window of WINDOW beats
            if len(self._rr_intervals) > WINDOW:
                self._rr_intervals.pop(0)
            self._update_stats()

        self._last_beat_ts = now
        self._row_beats._val.setText(str(self._beat_count))

    def _update_stats(self):
        rr = self._rr_intervals
        if not rr:
            return

        # BPM: average of the window's RR intervals, converted to beats/min.
        # Averaging RR first (not BPM) is the physiologically correct method —
        # averaging BPM values directly introduces a bias toward higher rates.
        avg_rr_ms = sum(rr) / len(rr)
        bpm = round(60_000 / avg_rr_ms)
        self._row_bpm._val.setText(str(bpm))

        # HRV (SDNN proxy): std dev of RR intervals in ms.
        # Only meaningful with ≥2 samples; shown from first two beats onward.
        if len(rr) >= 2:
            mean = avg_rr_ms
            sd   = math.sqrt(sum((x - mean) ** 2 for x in rr) / len(rr))
            self._row_hrv._val.setText(f"{sd:.1f}")

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._sock.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PulseDashboard()
    win.show()
    sys.exit(app.exec())