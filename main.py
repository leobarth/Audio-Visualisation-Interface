import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import pyaudio
import numpy as np
import queue
import time
import json

# --- CONFIG ---
CHUNK = 1024
RATE = 44100
FREQ_MIN = 2000
FREQ_MAX = 8000
OVERLAP_FACTOR = 4
DRAW_TIME = 20

class AudioAnalyzer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Analyzer")
        self.resize(1300, 900)

        self.data_queue = queue.Queue()
        self.audio_buffer = np.zeros(CHUNK)
        self.running_max = 500
        self.prev_bars = None
        self.peaks = None 
        self.peak_times = None
        self.SETTINGS = self.loadSettings()
        
        self.init_ui()
        self.init_audio()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.process_audio)
        self.timer.start(DRAW_TIME)

    def init_ui(self):
        main_layout = QtWidgets.QHBoxLayout(self)
        controls_group = QtWidgets.QGroupBox("Controls")
        controls_group.setFixedWidth(300)
        v_layout = QtWidgets.QVBoxLayout()

        # GROUP 1: CALIBRATION
        v_layout.addWidget(QtWidgets.QLabel("<b>CALIBRATION</b>"))
        self.btn_running_toggle = QtWidgets.QPushButton("Auto-Calibration: ON")
        self.btn_running_toggle.setCheckable(True); self.btn_running_toggle.setChecked(self.SETTINGS["AUTO_CALIBRATION_ON"])
        v_layout.addWidget(self.btn_running_toggle)
        self.label_ref = QtWidgets.QLabel("Full Scale")
        v_layout.addWidget(self.label_ref)
        self.slider_ref = self.create_slider(100, 5000, self.SETTINGS["FULL_SCALE_VALUE"])
        v_layout.addWidget(self.slider_ref)
        self.label_gate = QtWidgets.QLabel("Noise Gate")
        v_layout.addWidget(self.label_gate)
        self.slider_gate = self.create_slider(0, 30, self.SETTINGS["NOISE_GATE_VALUE"])
        v_layout.addWidget(self.slider_gate)

        # GROUP 2: EQUALIZER
        v_layout.addSpacing(10); v_layout.addWidget(QtWidgets.QLabel("<b>EQUALIZER</b>"))
        self.btn_eq_toggle = QtWidgets.QPushButton("EQ: ON")
        self.btn_eq_toggle.setCheckable(True); self.btn_eq_toggle.setChecked(self.SETTINGS["EQUALIZER_ON"])
        v_layout.addWidget(self.btn_eq_toggle)
        self.label_low = QtWidgets.QLabel("Lows"); self.slider_low = self.create_slider(0, 40, self.SETTINGS["LOWS_VALUE"])
        v_layout.addWidget(self.label_low); v_layout.addWidget(self.slider_low)
        self.label_mid = QtWidgets.QLabel("Mids"); self.slider_mid = self.create_slider(0, 40, self.SETTINGS["MIDS_VALUE"])
        v_layout.addWidget(self.label_mid); v_layout.addWidget(self.slider_mid)
        self.label_high = QtWidgets.QLabel("Highs"); self.slider_high = self.create_slider(0, 40, self.SETTINGS["HIGHS_VALUE"])
        v_layout.addWidget(self.label_high); v_layout.addWidget(self.slider_high)

        # GROUP 3: BALLISTICS
        v_layout.addSpacing(10); v_layout.addWidget(QtWidgets.QLabel("<b>BALLISTICS</b>"))
        self.btn_ballistics_toggle = QtWidgets.QPushButton("Ballistics: ON")
        self.btn_ballistics_toggle.setCheckable(True); self.btn_ballistics_toggle.setChecked(self.SETTINGS["BALLISTICS_ON"])
        v_layout.addWidget(self.btn_ballistics_toggle)
        self.label_attack = QtWidgets.QLabel("Attack"); self.slider_attack = self.create_slider(1, 100, self.SETTINGS["ATTACK_VALUE"])
        v_layout.addWidget(self.label_attack); v_layout.addWidget(self.slider_attack)
        self.label_release = QtWidgets.QLabel("Release"); self.slider_release = self.create_slider(0, 99, self.SETTINGS["RELEASE_VALUE"])
        v_layout.addWidget(self.label_release); v_layout.addWidget(self.slider_release)

        # GROUP 4: PEAK HOLD & GAIN
        v_layout.addSpacing(10); v_layout.addWidget(QtWidgets.QLabel("<b>PEAKS & GAIN</b>"))
        self.btn_peak_toggle = QtWidgets.QPushButton("Peak-Hold: ON")
        self.btn_peak_toggle.setCheckable(True); self.btn_peak_toggle.setChecked(self.SETTINGS["PEAK_HOLD_ON"])
        v_layout.addWidget(self.btn_peak_toggle)
        self.label_peak_hold = QtWidgets.QLabel("Peak Hold Duration")
        self.slider_peak_hold = self.create_slider(0, 30, self.SETTINGS["PEAK_HOLD_DURATION_VALUE"])
        v_layout.addWidget(self.label_peak_hold); v_layout.addWidget(self.slider_peak_hold)
        self.btn_gain_toggle = QtWidgets.QPushButton("Master Gain: ON")
        self.btn_gain_toggle.setCheckable(True); self.btn_gain_toggle.setChecked(self.SETTINGS["MASTER_GAIN_ON"])
        v_layout.addWidget(self.btn_gain_toggle)
        self.label_gain = QtWidgets.QLabel("Master Gain"); self.slider_gain = self.create_slider(1, 100, self.SETTINGS["MASTER_GAIN_VALUE"])
        v_layout.addWidget(self.label_gain); v_layout.addWidget(self.slider_gain)
        self.label_bin = QtWidgets.QLabel("Binning"); self.slider_bin = self.create_slider(1, 32, self.SETTINGS["BINNING_VALUE"])
        v_layout.addWidget(self.label_bin); v_layout.addWidget(self.slider_bin)

        v_layout.addStretch(); controls_group.setLayout(v_layout); main_layout.addWidget(controls_group)
        self.win = pg.GraphicsLayoutWidget()
        self.plot = self.win.addPlot(title="Spectral Analyzer"); self.plot.setYRange(0, 1.1)
        self.plot.showGrid(x=False, y=True, alpha=0.3)
        self.plot.setXRange(FREQ_MIN, FREQ_MAX, padding=0)
        self.bars = pg.BarGraphItem(x=[], height=[], width=1)
        self.peak_bars = pg.BarGraphItem(x=[], height=[], width=1, brush='w')
        self.plot.addItem(self.bars); self.plot.addItem(self.peak_bars)
        main_layout.addWidget(self.win)
        
        # Connections
        self.btn_running_toggle.toggled.connect(self.on_calibration_toggled)
        self.btn_eq_toggle.toggled.connect(self.on_eq_toggled)
        self.btn_ballistics_toggle.toggled.connect(self.on_ballistics_toggled)
        self.btn_peak_toggle.toggled.connect(self.on_peak_toggled)
        self.btn_gain_toggle.toggled.connect(self.on_gain_toggled)
        for s in [self.slider_ref, self.slider_gate, self.slider_attack, self.slider_release, 
                  self.slider_peak_hold, self.slider_gain, self.slider_bin, self.slider_low, self.slider_mid, self.slider_high]:
            s.valueChanged.connect(self.update_labels)
        self.update_labels()

    def create_slider(self, min_v, max_v, start_v):
        s = QtWidgets.QSlider(QtCore.Qt.Horizontal); s.setRange(min_v, max_v); s.setValue(start_v); return s

    def on_calibration_toggled(self, checked): self.slider_ref.setEnabled(not checked); self.update_labels()
    def on_eq_toggled(self, checked):
        for s in [self.slider_low, self.slider_mid, self.slider_high]: s.setEnabled(checked)
        self.update_labels()
    def on_ballistics_toggled(self, checked): self.slider_attack.setEnabled(checked); self.slider_release.setEnabled(checked); self.update_labels()
    def on_peak_toggled(self, checked):
        self.slider_peak_hold.setEnabled(checked)
        if not checked:
            self.peaks = None; self.peak_times = None
            self.peak_bars.setOpts(height=np.zeros(1), y0=np.zeros(1), visible=False) # Reset & Hide
        self.update_labels()
    def on_gain_toggled(self, checked): self.slider_gain.setEnabled(checked); self.update_labels()

    def update_labels(self):
        self.btn_running_toggle.setText(f"Auto-Calibration: {'ON' if self.btn_running_toggle.isChecked() else 'OFF'}")
        self.btn_eq_toggle.setText(f"EQ: {'ON' if self.btn_eq_toggle.isChecked() else 'OFF'}")
        self.btn_ballistics_toggle.setText(f"Ballistics: {'ON' if self.btn_ballistics_toggle.isChecked() else 'OFF'}")
        self.btn_peak_toggle.setText(f"Peak-Hold: {'ON' if self.btn_peak_toggle.isChecked() else 'OFF'}")
        self.btn_gain_toggle.setText(f"Master Gain: {'ON' if self.btn_gain_toggle.isChecked() else 'OFF'}")
        is_a = self.btn_running_toggle.isChecked()
        self.label_ref.setText(f"Full Scale ({self.slider_ref.value()})")
        self.label_gate.setText(f"Noise Gate ({'Relative' if is_a else 'Absolute'}: {self.slider_gate.value() if is_a else int(self.slider_ref.value()*self.slider_gate.value()/100.0)}{'%' if is_a else ''})")
        self.label_low.setText(f"Lows: {self.slider_low.value()/10.0:.1f}x"); self.label_mid.setText(f"Mids: {self.slider_mid.value()/10.0:.1f}x"); self.label_high.setText(f"Highs: {self.slider_high.value()/10.0:.1f}x")
        self.label_gain.setText(f"Master Gain: {self.slider_gain.value()/10.0:.1f}x"); self.label_peak_hold.setText(f"Hold Duration: {self.slider_peak_hold.value()/10.0:.1f}s")
        self.label_attack.setText(f"Attack: {self.slider_attack.value()/100.0:.2f}"); self.label_release.setText(f"Release: {self.slider_release.value()/100.0:.2f}"); self.label_bin.setText(f"Binning: {self.slider_bin.value()}")

    def init_audio(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK // OVERLAP_FACTOR, stream_callback=self.audio_callback)
    def audio_callback(self, in_data, frame_count, time_info, status): self.data_queue.put(in_data); return (None, pyaudio.paContinue)
    def process_audio(self):
        while not self.data_queue.empty():
            new_data = np.frombuffer(self.data_queue.get_nowait(), dtype=np.int16)
            self.audio_buffer = np.roll(self.audio_buffer, -len(new_data))
            self.audio_buffer[-len(new_data):] = new_data
            self.update_plot()

    def update_plot(self):
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

        if self.btn_running_toggle.isChecked(): self.running_max = max(self.running_max*0.98 + np.max(b_fft)*0.02, 500); ref = self.running_max
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
        # Kein else-Zweig hier nötig, da on_peak_toggled das Item bereits versteckt

    def closeEvent(self, event): self.stream.stop_stream(); self.stream.close(); self.updateSettings(); self.writeSettingsToFile(); self.p.terminate(); event.accept()
    
    def loadSettings(self):
        with open("settings.json", "r") as f:
            settings = json.load(f)
            return settings
    def updateSettings(self):
        self.SETTINGS["AUTO_CALIBRATION_ON"] = self.btn_running_toggle.isChecked()
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

if __name__ == '__main__':
    app = QtWidgets.QApplication([]); analyzer = AudioAnalyzer(); analyzer.show(); app.exec()