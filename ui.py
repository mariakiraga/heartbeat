"""
ui.py  —  Pulse & Breath Dashboard
Listens for BEAT on UDP 5006 (sent by bridge.py).

Dependencies:
    pip install PyQt6 pyqtgraph numpy
"""

import sys, socket, time, math
import numpy as np
import pyqtgraph as pg

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QComboBox,
)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath

# ── Palette ───────────────────────────────────────────────────────────────────

DARK = {
    "bg":     "#12121A", "panel":  "#1C1C28",
    "border": "#2C2C3C", "sage":   "#7a9e8e",
    "sage_d": "#1e2e28", "rose":   "#c4847a",
    "rose_d": "#2e1e1c", "cream":  "#d8d4cc",
    "muted":  "#666660", "faint":  "#252525",
    "wave":   "#c4847a",
}
LIGHT = {
    "bg":     "#F2EFE9", "panel":  "#FFFFFF",
    "border": "#E0DAD0", "sage":   "#5a8070",
    "sage_d": "#e4f0ea", "rose":   "#b06a60",
    "rose_d": "#f5e0dc", "cream":  "#282420",
    "muted":  "#888880", "faint":  "#ece8e0",
    "wave":   "#b06a60",
}

TECHNIQUES = {
    "Off": None,
    "Coherent 5-5": [
        {"name": "inhale", "dur": 5.0},
        {"name": "exhale", "dur": 5.0},
    ],
    "4-7-8": [
        {"name": "inhale", "dur": 4.0},
        {"name": "hold",   "dur": 7.0},
        {"name": "exhale", "dur": 8.0},
    ],
    "Box 4×4": [
        {"name": "inhale", "dur": 4.0},
        {"name": "hold",   "dur": 4.0},
        {"name": "exhale", "dur": 4.0},
        {"name": "hold",   "dur": 4.0},
    ],
    "2-4-6": [
        {"name": "inhale", "dur": 2.0},
        {"name": "hold",   "dur": 4.0},
        {"name": "exhale", "dur": 6.0},
    ],
}

PHASE_HEX = {"inhale": "#7a9e8e", "hold": "#a8c4b8", "exhale": "#c4847a"}


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
        self._beat_col = QColor(beat); self._rest_col = QColor(rest); self.update()

    def _step(self):
        if self._scale > 1.002:
            self._scale += (1.0 - self._scale) * 0.16; self.update()
        elif self._active:
            self._active = False; self._scale = 1.0

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, s = self.width()/2, self.height()/2, self._scale
        r = 36 * s
        p.setPen(QPen(self._beat_col, 1.0))
        p.setBrush(QBrush(self._beat_col if self._active else self._rest_col))
        p.drawEllipse(QPointF(cx, cy), r, r)

        path = QPainterPath()
        pts = []
        for i in range(100):
            t  = 2 * math.pi * i / 99
            hx = 16 * math.sin(t) ** 3
            hy = -(13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t))
            pts.append((cx + hx*1.2*s, cy + hy*1.2*s))
        path.moveTo(*pts[0])
        for px, py in pts[1:]: path.lineTo(px, py)
        path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._beat_col))
        p.drawPath(path)


# ── Breath orb ────────────────────────────────────────────────────────────────

class BreathOrb(QWidget):
    SIZE = 220

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self._progress = 0.0; self._orb_r = 0.35
        self._arc  = QColor("#7a9e8e"); self._track = QColor("#252525")
        self._inner = QColor("#1e2e28"); self._bdr   = QColor("#7a9e8e")

    def set_state(self, progress, orb_r, arc, track, inner, bdr):
        self._progress = max(0.0, min(1.0, progress))
        self._orb_r    = max(0.0, min(1.0, orb_r))
        self._arc      = QColor(arc);   self._track = QColor(track)
        self._inner    = QColor(inner); self._bdr   = QColor(bdr)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width()/2, self.height()/2
        R = min(self.width(), self.height())/2 - 10
        p.setPen(QPen(self._track, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), R, R)
        if self._progress > 0:
            p.setPen(QPen(self._arc, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawArc(int(cx-R), int(cy-R), int(2*R), int(2*R),
                      90*16, int(-self._progress*360*16))
        r_min, r_max = R*0.28, R*0.64
        r = r_min + (r_max - r_min) * self._orb_r
        p.setPen(QPen(self._bdr, 1)); p.setBrush(QBrush(self._inner))
        p.drawEllipse(QPointF(cx, cy), r, r)


# ── Separator line ────────────────────────────────────────────────────────────

def hline(parent=None):
    f = QFrame(parent)
    f.setFrameShape(QFrame.Shape.HLine)
    f.setObjectName("sep")
    return f


# ── Main window ───────────────────────────────────────────────────────────────

class PulseDashboard(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("pulse & breath")
        self.setFixedSize(780, 500)

        self._theme   = DARK; self._is_dark = True
        self._mode    = "monitor"; self._paused = False

        self._beat_count   = 0
        self._last_beat_ts = None
        self._bpm_history  = []

        self._breath_tech    = "Off"
        self._breath_running = False
        self._breath_phase_i = 0
        self._breath_phase_t = 0.0
        self._breath_orb_r   = 0.35

        self._buf  = 400
        self._wavy = np.zeros(self._buf)
        self._wavx = np.arange(self._buf)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("127.0.0.1", 5006))
        self._sock.setblocking(False)

        self._build_ui()
        self._apply_theme()

        self._timer = QTimer(self)
        self._timer.setInterval(20)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        vroot = QVBoxLayout(root)
        vroot.setContentsMargins(16, 14, 16, 14)
        vroot.setSpacing(10)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QHBoxLayout(); toolbar.setSpacing(8)

        self._lbl_title = QLabel("pulse & breath")
        self._lbl_title.setObjectName("title")
        toolbar.addWidget(self._lbl_title)
        toolbar.addStretch()

        self._btn_mon   = self._tab_btn("monitor")
        self._btn_relax = self._tab_btn("relax")
        self._btn_mon.clicked.connect(lambda: self._set_mode("monitor"))
        self._btn_relax.clicked.connect(lambda: self._set_mode("relax"))
        toolbar.addWidget(self._btn_mon)
        toolbar.addWidget(self._btn_relax)

        self._btn_pause = QPushButton("pause")
        self._btn_pause.setCheckable(True)
        self._btn_pause.setObjectName("smallBtn")
        self._btn_pause.clicked.connect(self._toggle_pause)
        toolbar.addWidget(self._btn_pause)

        self._btn_theme = QPushButton("☀")
        self._btn_theme.setObjectName("smallBtn")
        self._btn_theme.setFixedWidth(34)
        self._btn_theme.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self._btn_theme)

        vroot.addLayout(toolbar)
        vroot.addWidget(hline())

        # ── Monitor view ──────────────────────────────────────────────────────
        self._mon_view = QWidget()
        mv = QHBoxLayout(self._mon_view)
        mv.setContentsMargins(0, 0, 0, 0)
        mv.setSpacing(16)

        # Left: heart + stats
        left = QVBoxLayout(); left.setSpacing(12)
        left.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._heart = HeartOrb()
        left.addWidget(self._heart, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Stats: three rows, small font
        stats_frame = QFrame(); stats_frame.setObjectName("card")
        sf = QVBoxLayout(stats_frame)
        sf.setContentsMargins(14, 10, 14, 10); sf.setSpacing(4)
        self._lbl_bpm  = self._stat_row("bpm",      "--")
        self._lbl_cnt  = self._stat_row("beats",     "0")
        self._lbl_last = self._stat_row("interval",  "--")
        for row in (self._lbl_bpm, self._lbl_cnt, self._lbl_last):
            sf.addLayout(row)
        left.addWidget(stats_frame)
        left.addStretch()

        mv.addLayout(left)

        # Right: waveform
        self._wplot = pg.PlotWidget()
        self._wplot.setYRange(-1.4, 1.4)
        self._wplot.getPlotItem().hideAxis("bottom")
        self._wplot.getPlotItem().hideAxis("left")
        self._wplot.showGrid(x=False, y=False)
        self._wline = self._wplot.plot(self._wavx, self._wavy)
        mv.addWidget(self._wplot, stretch=1)

        vroot.addWidget(self._mon_view, stretch=1)

        # ── Relax view ────────────────────────────────────────────────────────
        self._rel_view = QWidget(); self._rel_view.hide()
        rv = QHBoxLayout(self._rel_view)
        rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(24)

        # Orb centred
        orb_v = QVBoxLayout()
        orb_v.setAlignment(Qt.AlignmentFlag.AlignCenter); orb_v.setSpacing(6)
        self._borb = BreathOrb()
        self._lbl_bword  = QLabel("ready"); self._lbl_bword.setObjectName("breathWord")
        self._lbl_bcount = QLabel("");      self._lbl_bcount.setObjectName("breathCount")
        for w in (self._borb, self._lbl_bword, self._lbl_bcount):
            orb_v.addWidget(w, alignment=Qt.AlignmentFlag.AlignHCenter)
        rv.addLayout(orb_v)

        # Controls beside orb
        ctrl_frame = QFrame(); ctrl_frame.setObjectName("card")
        ctrl_frame.setFixedWidth(180)
        cf = QVBoxLayout(ctrl_frame)
        cf.setContentsMargins(14, 14, 14, 14); cf.setSpacing(10)

        lbl_t = QLabel("technique"); lbl_t.setObjectName("micro")
        cf.addWidget(lbl_t)
        self._combo = QComboBox()
        self._combo.addItems(list(TECHNIQUES.keys()))
        self._combo.currentTextChanged.connect(self._change_tech)
        cf.addWidget(self._combo)

        self._lbl_desc = QLabel(""); self._lbl_desc.setObjectName("micro")
        self._lbl_desc.setWordWrap(True)
        cf.addWidget(self._lbl_desc)

        cf.addStretch()

        self._btn_breath = QPushButton("start")
        self._btn_breath.setObjectName("accentBtn")
        self._btn_breath.clicked.connect(self._toggle_breath)
        cf.addWidget(self._btn_breath)

        rv.addWidget(ctrl_frame, alignment=Qt.AlignmentFlag.AlignVCenter)
        vroot.addWidget(self._rel_view, stretch=1)

        self._set_mode("monitor")

    def _tab_btn(self, text):
        b = QPushButton(text); b.setObjectName("tabBtn"); return b

    def _stat_row(self, label, val):
        row = QHBoxLayout(); row.setSpacing(8)
        lbl = QLabel(label); lbl.setObjectName("micro")
        val_lbl = QLabel(val); val_lbl.setObjectName("statVal")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(lbl); row.addStretch(); row.addWidget(val_lbl)
        # Store reference on the value label so we can update it
        row._val_lbl = val_lbl
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
            #sep {{ color: {t['border']}; }}
            #title {{
                font-family: Georgia; font-size: 15px; color: {t['cream']};
            }}
            #statVal {{
                font-family: Georgia; font-size: 13px; color: {t['cream']};
            }}
            #micro {{
                font-family: Helvetica; font-size: 10px; color: {t['muted']};
            }}
            #breathWord {{
                font-family: Georgia; font-size: 18px; color: {t['cream']};
            }}
            #breathCount {{
                font-family: Georgia; font-size: 30px; color: {t['sage']};
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
            #tabBtn {{ border-radius: 14px; padding: 4px 14px; }}
            #smallBtn {{ padding: 4px 10px; }}
            #accentBtn {{
                background-color: {t['sage_d']}; color: {t['sage']};
                border-color: {t['sage']}; padding: 7px 12px;
            }}
            #accentBtn:hover {{
                background-color: {t['sage']}; color: {t['bg']};
            }}
            QComboBox {{
                background-color: {t['panel']}; color: {t['cream']};
                border: 1px solid {t['border']}; border-radius: 7px;
                padding: 5px 8px; font-size: 11px; font-family: Helvetica;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['panel']}; color: {t['cream']};
                selection-background-color: {t['sage_d']};
            }}
        """)
        self._wplot.setBackground(t["bg"])
        self._wline.setPen(pg.mkPen(color=t["wave"], width=1.5))
        self._heart.set_palette(t["rose"], t["rose_d"])
        self._borb.set_state(
            self._borb._progress, self._borb._orb_r,
            t["sage"], t["faint"], t["sage_d"], t["sage"],
        )
        self._refresh_tabs()

    def _refresh_tabs(self):
        t = self._theme
        on  = f"background-color:{t['sage_d']}; color:{t['sage']}; border-color:{t['sage']};"
        off = ""
        self._btn_mon.setStyleSheet(on   if self._mode == "monitor" else off)
        self._btn_relax.setStyleSheet(on if self._mode == "relax"   else off)

    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        self._theme   = DARK if self._is_dark else LIGHT
        self._btn_theme.setText("☀" if self._is_dark else "☾")
        self._apply_theme()

    # ── Mode ──────────────────────────────────────────────────────────────────

    def _set_mode(self, mode):
        self._mode = mode
        self._mon_view.setVisible(mode == "monitor")
        self._rel_view.setVisible(mode == "relax")
        self._refresh_tabs()

    # ── Controls ──────────────────────────────────────────────────────────────

    def _toggle_pause(self):
        self._paused = self._btn_pause.isChecked()
        self._btn_pause.setText("resume" if self._paused else "pause")

    def _change_tech(self, text):
        self._breath_tech    = text
        self._breath_phase_i = 0
        self._breath_phase_t = 0.0
        phases = TECHNIQUES.get(text)
        self._lbl_desc.setText(
            " · ".join(f"{p['name']} {int(p['dur'])}s" for p in phases)
            if phases else ""
        )
        if not self._breath_running:
            self._lbl_bword.setText("ready")
            self._lbl_bcount.setText("")
            self._set_borb(0.0, 0.35, self._theme["sage"])

    def _toggle_breath(self):
        if self._breath_running:
            self._breath_running = False
            self._btn_breath.setText("start")
            self._breath_phase_i = 0; self._breath_phase_t = 0.0
            self._lbl_bword.setText("ready"); self._lbl_bcount.setText("")
            self._set_borb(0.0, 0.35, self._theme["sage"])
        else:
            if not TECHNIQUES.get(self._breath_tech):
                return
            self._breath_running = True
            self._btn_breath.setText("stop")
            self._breath_phase_i = 0; self._breath_phase_t = 0.0

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick(self):
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

        # Waveform scroll — small noise baseline, spike on beat
        self._wavy = np.roll(self._wavy, -1)
        self._wavy[-1] = 0.80 if beat else np.random.uniform(-0.04, 0.04)
        self._wline.setData(self._wavx, self._wavy)
        if beat:
            QTimer.singleShot(50,  lambda: self._push_wave(-0.65))
            QTimer.singleShot(100, lambda: self._push_wave(0.0))

        if self._breath_running:
            self._step_breath(0.020)

    def _push_wave(self, val):
        self._wavy = np.roll(self._wavy, -1)
        self._wavy[-1] = val
        self._wline.setData(self._wavx, self._wavy)

    def _on_beat(self):
        now = time.time()
        self._beat_count += 1
        self._heart.beat()

        if self._last_beat_ts is not None:
            iv  = now - self._last_beat_ts
            bpm = int(60 / iv)
            self._bpm_history.append(bpm)
            if len(self._bpm_history) > 6:
                self._bpm_history.pop(0)
            avg = round(sum(self._bpm_history) / len(self._bpm_history))
            self._lbl_bpm._val_lbl.setText(f"{avg}")
            self._lbl_last._val_lbl.setText(f"{iv:.1f}s")

        self._last_beat_ts = now
        self._lbl_cnt._val_lbl.setText(str(self._beat_count))

    # ── Breathing ─────────────────────────────────────────────────────────────

    def _step_breath(self, dt):
        phases = TECHNIQUES.get(self._breath_tech)
        if not phases:
            return
        idx   = self._breath_phase_i % len(phases)
        phase = phases[idx]
        dur, name = phase["dur"], phase["name"]
        self._breath_phase_t += dt
        t = min(self._breath_phase_t / dur, 1.0)

        target_r = 1.0 if name == "inhale" else (0.0 if name == "exhale" else self._breath_orb_r)
        self._breath_orb_r += (target_r - self._breath_orb_r) * min(dt / dur * 4.5, 0.12)
        self._breath_orb_r  = max(0.0, min(1.0, self._breath_orb_r))

        self._set_borb(t, self._breath_orb_r, PHASE_HEX.get(name, self._theme["sage"]))
        self._lbl_bword.setText(name)
        self._lbl_bcount.setText(str(max(0, math.ceil(dur - self._breath_phase_t))))

        if self._breath_phase_t >= dur:
            self._breath_phase_i += 1; self._breath_phase_t = 0.0

    def _set_borb(self, progress, orb_r, color):
        t = self._theme
        self._borb.set_state(progress, orb_r, color, t["faint"], t["sage_d"], t["sage"])

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._sock.close(); event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PulseDashboard()
    win.show()
    sys.exit(app.exec())