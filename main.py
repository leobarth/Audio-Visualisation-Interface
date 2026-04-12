import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
import pyaudio
import numpy as np
import queue
import time
import json
import ctypes
import platform

# --- CONFIG ---
CHUNK = 2048
RATE = 44100
FREQ_MIN = 2000
FREQ_MAX = 8000
OVERLAP_FACTOR = 4
DRAW_TIME = 20

def makeDpiAware():
    if int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

class AudioAnalyzer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Analyzer")

        self.data_queue = queue.Queue()
        self.audio_buffer = np.zeros(CHUNK)
        self.running_max = 500
        self.prev_bars = None
        self.peaks = None 
        self.peak_times = None
        self.SETTINGS = self.loadSettingsFromFile()
        
        self.initUI()
        self.resize(1500, 300)
        self.initAudio()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.processAudio)
        self.timer.start(DRAW_TIME)
        
        self.shortcut_hide = QShortcut(QKeySequence("H"), self)
        self.shortcut_hide.activated.connect(self.toggleHiddenUI)
        
    def centerOnPrimaryScreen(self):
        desktop = QtWidgets.QApplication.desktop()
        screen_rect = desktop.availableGeometry(0)
        screen_center = screen_rect.center()
        window_rect = self.frameGeometry()
        window_rect.moveCenter(screen_center)
        self.move(window_rect.topLeft())

    def initUI(self):
        self.sidebar_width = 300
        scroll_padding = 42
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.controls_group = QtWidgets.QGroupBox("Controls")
        self.controls_group.setFixedWidth(self.sidebar_width)
        v_layout = QtWidgets.QVBoxLayout()
        
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedWidth(self.sidebar_width + scroll_padding)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        # GROUP 1: NORMALISATION (Calibration)
        v_layout.addWidget(QtWidgets.QLabel("<b>NORMALISATION</b>"))
        self.btn_calibration_toggle = QtWidgets.QPushButton("Manual Calibration: ON")
        self.btn_calibration_toggle.setCheckable(True); self.btn_calibration_toggle.setChecked(self.SETTINGS["MANUAL_CALIBRATION_ON"])
        v_layout.addWidget(self.btn_calibration_toggle)
        self.label_ref = QtWidgets.QLabel("Full Scale")
        v_layout.addWidget(self.label_ref)
        self.slider_ref = self.createSlider(100, 5000, self.SETTINGS["FULL_SCALE_VALUE"])
        v_layout.addWidget(self.slider_ref)
        self.label_gate = QtWidgets.QLabel("Noise Gate")
        v_layout.addWidget(self.label_gate)
        self.slider_gate = self.createSlider(0, 30, self.SETTINGS["NOISE_GATE_VALUE"])
        v_layout.addWidget(self.slider_gate)

        # GROUP 2: EQUALIZER
        v_layout.addSpacing(10); v_layout.addWidget(QtWidgets.QLabel("<b>EQUALIZER</b>"))
        self.btn_eq_toggle = QtWidgets.QPushButton("EQ: ON")
        self.btn_eq_toggle.setCheckable(True); self.btn_eq_toggle.setChecked(self.SETTINGS["EQUALIZER_ON"])
        v_layout.addWidget(self.btn_eq_toggle)
        self.label_low = QtWidgets.QLabel("Lows"); self.slider_low = self.createSlider(0, 40, self.SETTINGS["LOWS_VALUE"])
        v_layout.addWidget(self.label_low); v_layout.addWidget(self.slider_low)
        self.label_mid = QtWidgets.QLabel("Mids"); self.slider_mid = self.createSlider(0, 40, self.SETTINGS["MIDS_VALUE"])
        v_layout.addWidget(self.label_mid); v_layout.addWidget(self.slider_mid)
        self.label_high = QtWidgets.QLabel("Highs"); self.slider_high = self.createSlider(0, 40, self.SETTINGS["HIGHS_VALUE"])
        v_layout.addWidget(self.label_high); v_layout.addWidget(self.slider_high)

        # GROUP 3: BALLISTICS
        v_layout.addSpacing(10); v_layout.addWidget(QtWidgets.QLabel("<b>BALLISTICS</b>"))
        self.btn_ballistics_toggle = QtWidgets.QPushButton("Ballistics: ON")
        self.btn_ballistics_toggle.setCheckable(True); self.btn_ballistics_toggle.setChecked(self.SETTINGS["BALLISTICS_ON"])
        v_layout.addWidget(self.btn_ballistics_toggle)
        self.label_attack = QtWidgets.QLabel("Attack"); self.slider_attack = self.createSlider(1, 100, self.SETTINGS["ATTACK_VALUE"])
        v_layout.addWidget(self.label_attack); v_layout.addWidget(self.slider_attack)
        self.label_release = QtWidgets.QLabel("Release"); self.slider_release = self.createSlider(0, 99, self.SETTINGS["RELEASE_VALUE"])
        v_layout.addWidget(self.label_release); v_layout.addWidget(self.slider_release)

        # GROUP 4: PEAK HOLD & GAIN
        v_layout.addSpacing(10); v_layout.addWidget(QtWidgets.QLabel("<b>PEAKS & GAIN</b>"))
        self.btn_peak_toggle = QtWidgets.QPushButton("Peak-Hold: ON")
        self.btn_peak_toggle.setCheckable(True); self.btn_peak_toggle.setChecked(self.SETTINGS["PEAK_HOLD_ON"])
        v_layout.addWidget(self.btn_peak_toggle)
        self.label_peak_hold = QtWidgets.QLabel("Peak Hold Duration")
        self.slider_peak_hold = self.createSlider(0, 30, self.SETTINGS["PEAK_HOLD_DURATION_VALUE"])
        v_layout.addWidget(self.label_peak_hold); v_layout.addWidget(self.slider_peak_hold)
        self.btn_gain_toggle = QtWidgets.QPushButton("Master Gain: ON")
        self.btn_gain_toggle.setCheckable(True); self.btn_gain_toggle.setChecked(self.SETTINGS["MASTER_GAIN_ON"])
        v_layout.addWidget(self.btn_gain_toggle)
        self.label_gain = QtWidgets.QLabel("Master Gain"); self.slider_gain = self.createSlider(1, 100, self.SETTINGS["MASTER_GAIN_VALUE"])
        v_layout.addWidget(self.label_gain); v_layout.addWidget(self.slider_gain)
        self.label_bin = QtWidgets.QLabel("Binning"); self.slider_bin = self.createSlider(1, 32, self.SETTINGS["BINNING_VALUE"])
        v_layout.addWidget(self.label_bin); v_layout.addWidget(self.slider_bin)

        v_layout.addStretch()
        self.controls_group.setLayout(v_layout)
        self.scroll.setWidget(self.controls_group)
        self.main_layout.addWidget(self.scroll)
        
        self.win = pg.GraphicsLayoutWidget()
        self.plot = self.win.addPlot(); self.plot.setYRange(0, 1.1)
        self.plot.showGrid(x=False, y=True, alpha=0.3)
        self.plot.setXRange(FREQ_MIN, FREQ_MAX, padding=0)
        self.bars = pg.BarGraphItem(x=[], height=[], width=1)
        self.peak_bars = pg.BarGraphItem(x=[], height=[], width=1, brush='w')
        self.plot.addItem(self.bars); self.plot.addItem(self.peak_bars)
        self.main_layout.addWidget(self.win, 1)
        
        # Connections
        self.btn_calibration_toggle.toggled.connect(self.onCalibrationToggled)
        self.btn_eq_toggle.toggled.connect(self.onEqToggled)
        self.btn_ballistics_toggle.toggled.connect(self.onBallisticsToggled)
        self.btn_peak_toggle.toggled.connect(self.onPeakToggled)
        self.btn_gain_toggle.toggled.connect(self.onGainToggled)
        for s in [self.slider_ref, self.slider_gate, self.slider_attack, self.slider_release, 
                  self.slider_peak_hold, self.slider_gain, self.slider_bin, self.slider_low, self.slider_mid, self.slider_high]:
            s.valueChanged.connect(self.updateLabels)
        self.updateLabels()
        self.syncSlidersToTogglesOnInit()

    def createSlider(self, min_v, max_v, start_v):
        s = QtWidgets.QSlider(QtCore.Qt.Horizontal); s.setRange(min_v, max_v); s.setValue(start_v); return s

    def onCalibrationToggled(self, checked): self.slider_ref.setEnabled(checked); self.updateLabels()
    def onEqToggled(self, checked):
        for s in [self.slider_low, self.slider_mid, self.slider_high]: s.setEnabled(checked)
        self.updateLabels()
    def onBallisticsToggled(self, checked): self.slider_attack.setEnabled(checked); self.slider_release.setEnabled(checked); self.updateLabels()
    def onPeakToggled(self, checked):
        self.slider_peak_hold.setEnabled(checked)
        if not checked:
            self.peaks = None; self.peak_times = None
            self.peak_bars.setOpts(height=np.zeros(1), y0=np.zeros(1), visible=False) # Reset & Hide
        self.updateLabels()
    def onGainToggled(self, checked): self.slider_gain.setEnabled(checked); self.updateLabels()
    
    def syncSlidersToTogglesOnInit(self):
        self.slider_ref.setEnabled(self.btn_calibration_toggle.isChecked())
        for s in [self.slider_low, self.slider_mid, self.slider_high]: s.setEnabled(self.btn_eq_toggle.isChecked())
        for s in [self.slider_attack, self.slider_release]: s.setEnabled(self.btn_ballistics_toggle.isChecked())
        self.slider_peak_hold.setEnabled(self.btn_peak_toggle.isChecked())
        self.slider_gain.setEnabled(self.btn_gain_toggle.isChecked())
        
    def toggleHiddenUI(self):
        if self.scroll.isVisible():
            self.scroll.hide()
        else:
            self.scroll.show()
        self.main_layout.activate()

    def updateLabels(self):
        self.btn_calibration_toggle.setText(f"Manual Calibration: {'ON' if self.btn_calibration_toggle.isChecked() else 'OFF'}")
        self.btn_eq_toggle.setText(f"EQ: {'ON' if self.btn_eq_toggle.isChecked() else 'OFF'}")
        self.btn_ballistics_toggle.setText(f"Ballistics: {'ON' if self.btn_ballistics_toggle.isChecked() else 'OFF'}")
        self.btn_peak_toggle.setText(f"Peak-Hold: {'ON' if self.btn_peak_toggle.isChecked() else 'OFF'}")
        self.btn_gain_toggle.setText(f"Master Gain: {'ON' if self.btn_gain_toggle.isChecked() else 'OFF'}")
        is_a = not self.btn_calibration_toggle.isChecked()
        self.label_ref.setText(f"Full Scale ({self.slider_ref.value()})")
        self.label_gate.setText(f"Noise Gate ({'Relative' if is_a else 'Absolute'}: {self.slider_gate.value() if is_a else int(self.slider_ref.value()*self.slider_gate.value()/100.0)}{'%' if is_a else ''})")
        self.label_low.setText(f"Lows: {self.slider_low.value()/10.0:.1f}x"); self.label_mid.setText(f"Mids: {self.slider_mid.value()/10.0:.1f}x"); self.label_high.setText(f"Highs: {self.slider_high.value()/10.0:.1f}x")
        self.label_gain.setText(f"Master Gain: {self.slider_gain.value()/10.0:.1f}x"); self.label_peak_hold.setText(f"Hold Duration: {self.slider_peak_hold.value()/10.0:.1f}s")
        self.label_attack.setText(f"Attack: {self.slider_attack.value()/100.0:.2f}"); self.label_release.setText(f"Release: {self.slider_release.value()/100.0:.2f}"); self.label_bin.setText(f"Binning: {self.slider_bin.value()}")

    def initAudio(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK // OVERLAP_FACTOR, stream_callback=self.audioCallback)
    def audioCallback(self, in_data, frame_count, time_info, status): self.data_queue.put(in_data); return (None, pyaudio.paContinue)
    def processAudio(self):
        while not self.data_queue.empty():
            new_data = np.frombuffer(self.data_queue.get_nowait(), dtype=np.int16)
            self.audio_buffer = np.roll(self.audio_buffer, -len(new_data))
            self.audio_buffer[-len(new_data):] = new_data
            self.updatePlot()

    def updatePlot(self):
        gain = (self.slider_gain.value()/10.0) if self.btn_gain_toggle.isChecked() else 1.0
        fft_d = np.abs(np.fft.rfft(self.audio_buffer * np.hanning(CHUNK)))
        freqs = np.fft.rfftfreq(CHUNK, 1.0/RATE)
        mask = (freqs >= FREQ_MIN) & (freqs <= FREQ_MAX)
        rel_fft, rel_f = fft_d[mask], freqs[mask]

        if self.btn_eq_toggle.isChecked():
            l_m, m_m, h_m = (rel_f < 3000), (rel_f >= 3000) & (rel_f < 5000), (rel_f >= 5000)
            rel_fft[l_m] *= (self.slider_low.value()/10.0); rel_fft[m_m] *= (self.slider_mid.value()/10.0); rel_fft[h_m] *= (self.slider_high.value()/10.0)

        c_bin = self.slider_bin.value(); n_bins = len(rel_fft) // c_bin
        if n_bins <= 0: return
        b_fft = rel_fft[:n_bins*c_bin].reshape(n_bins, c_bin).mean(axis=1)

        if self.btn_calibration_toggle.isChecked(): self.running_max = max(self.running_max*0.98 + np.max(b_fft)*0.02, 500); ref = self.running_max
        else: ref = self.slider_ref.value()
        b_fft[b_fft < (ref * self.slider_gate.value()/100.0)] = 0
        cur_norm = np.clip((b_fft * gain) / (ref + 1e-6), 0, 1)

        if self.btn_ballistics_toggle.isChecked():
            att, rle = self.slider_attack.value()/100.0, self.slider_release.value()/100.0
            if self.prev_bars is None or len(self.prev_bars) != n_bins: self.prev_bars = cur_norm
            else: self.prev_bars = np.where(cur_norm > self.prev_bars, (self.prev_bars*(1-att)) + (cur_norm*att), (self.prev_bars*rle) + (cur_norm*(1-rle)))
        else: self.prev_bars = cur_norm

        bin_w = (FREQ_MAX - FREQ_MIN) / n_bins; b_x = np.linspace(FREQ_MIN+bin_w/2, FREQ_MAX-bin_w/2, n_bins)
        self.bars.setOpts(x=b_x, height=self.prev_bars, width=bin_w, brushes=[pg.mkBrush(pg.intColor(i, n_bins)) for i in range(n_bins)])

        if self.btn_peak_toggle.isChecked():
            now, h_dur = time.time(), self.slider_peak_hold.value()/10.0
            if self.peaks is None or len(self.peaks) != n_bins: self.peaks = self.prev_bars.copy(); self.peak_times = np.full(n_bins, now)
            else:
                for i in range(n_bins):
                    if self.prev_bars[i] >= self.peaks[i]: self.peaks[i] = self.prev_bars[i]; self.peak_times[i] = now
                    elif now - self.peak_times[i] > h_dur: self.peaks[i] *= 0.95
            self.peak_bars.setOpts(x=b_x, height=np.full(n_bins, 0.01), y0=self.peaks, width=bin_w*0.8, visible=True)

    def closeEvent(self, event): self.stream.stop_stream(); self.stream.close(); self.updateSettings(); self.writeSettingsToFile(); self.p.terminate(); event.accept()
    
    def loadSettingsFromFile(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                return settings
        except:
            self.createDefaultSettingsFile()
            return self.loadSettingsFromFile()
    def updateSettings(self):
        self.SETTINGS["MANUAL_CALIBRATION_ON"] = self.btn_calibration_toggle.isChecked()
        self.SETTINGS["FULL_SCALE_VALUE"] = self.slider_ref.value()
        self.SETTINGS["NOISE_GATE_VALUE"] = self.slider_gate.value()
        self.SETTINGS["EQUALIZER_ON"] = self.btn_eq_toggle.isChecked()
        self.SETTINGS["LOWS_VALUE"] = self.slider_low.value()
        self.SETTINGS["MIDS_VALUE"] = self.slider_mid.value()
        self.SETTINGS["HIGHS_VALUE"] = self.slider_high.value()
        self.SETTINGS["BALLISTICS_ON"] = self.btn_ballistics_toggle.isChecked()
        self.SETTINGS["ATTACK_VALUE"] = self.slider_attack.value()
        self.SETTINGS["RELEASE_VALUE"] = self.slider_release.value()
        self.SETTINGS["PEAK_HOLD_ON"] = self.btn_peak_toggle.isChecked()
        self.SETTINGS["PEAK_HOLD_DURATION_VALUE"] = self.slider_peak_hold.value()
        self.SETTINGS["MASTER_GAIN_ON"] = self.btn_gain_toggle.isChecked()
        self.SETTINGS["MASTER_GAIN_VALUE"] = self.slider_gain.value()
        self.SETTINGS["BINNING_VALUE"] = self.slider_bin.value()
    def writeSettingsToFile(self):
        with open("settings.json", "w") as f:
            f.write(json.dumps(self.SETTINGS, indent=4))
    def createDefaultSettingsFile(self):
        with open("settings.json", "x") as f:
            default_settings = {
                "MANUAL_CALIBRATION_ON": True,
                "FULL_SCALE_VALUE": 2000,
                "NOISE_GATE_VALUE": 2,
                "EQUALIZER_ON": True,
                "LOWS_VALUE": 10,
                "MIDS_VALUE": 10,
                "HIGHS_VALUE": 10,
                "BALLISTICS_ON": True,
                "ATTACK_VALUE": 70,
                "RELEASE_VALUE": 95,
                "PEAK_HOLD_ON": True,
                "PEAK_HOLD_DURATION_VALUE": 5,
                "MASTER_GAIN_ON": False,
                "MASTER_GAIN_VALUE": 10,
                "BINNING_VALUE": 8
            }
            f.write(json.dumps(default_settings, indent=4))

if __name__ == '__main__':
    makeDpiAware()
    app = QtWidgets.QApplication([]); analyzer = AudioAnalyzer(); analyzer.show(); QtWidgets.QApplication.processEvents(); analyzer.centerOnPrimaryScreen(); app.exec()