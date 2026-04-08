# Audio Analyzer (PyAudio + PyQtGraph)

A real-time **spectrum analyzer / audio visualiser** written in Python.

`main.py` captures audio from your system’s **default input device** using **PyAudio**, performs an FFT on a rolling buffer, and renders a **color-coded bar spectrum** in a **PyQtGraph** window. A control panel lets you tune calibration, gating, EQ, smoothing (“ballistics”), peak-hold, and gain in real time.

---

## What the app shows

- A **bar-graph spectrum** for frequencies between **2 kHz and 8 kHz**
- Bars are **normalized** against either:
  - an **auto-calibrated running max**, or
  - a **manual full-scale reference**
- Optional **peak-hold markers** are drawn above the bars and fall to current amplitude level after a configurable hold time

---

## Controls

### Calibration
- **Auto-Calibration**: tracks a running maximum and uses it as the reference level
- **Full Scale**: manual reference value (enabled when auto-calibration is OFF)
- **Noise Gate**: suppresses quiet bins (relative to the current reference)

### Equalizer (simple band gains)
When **EQ** is ON, the spectrum bins are multiplied by:
- **Lows**: below ~3 kHz
- **Mids**: ~3–5 kHz
- **Highs**: above ~5 kHz

### Ballistics (smoothing)
When **Ballistics** is ON, the display is smoothed with:
- **Attack**: how quickly bars rise
- **Release**: how quickly bars fall

This makes the graph look more aesthetically appealing.

### Peaks & Gain
- **Peak-Hold**: shows recent peaks per bin for a configurable duration (then decays)
- **Peak Hold Duration**: hold time in seconds
- **Master Gain**: post-processing multiplier applied before normalization
- **Binning**: groups FFT bins together (averaging) to control bar count / visual density

---

## Requirements

- Python 3
- PyAudio (PortAudio)
- NumPy
- PyQtGraph
- Qt bindings (PyQt5 recommended)

---

## Installation

```bash
git clone https://github.com/leobarth/Audio-Visualisation-Interface.git
cd Audio-Visualisation-Interface

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install numpy pyaudio pyqtgraph PyQt5
```

> **Note (macOS / Linux):** PyAudio requires PortAudio
> - macOS: `brew install portaudio`
> - Ubuntu/Debian: `sudo apt-get install portaudio19-dev`

---

## Usage

Run:

```bash
python main.py
```

Close the window to save the current control values back to `settings.json`.

---

## How it works

- **Audio capture**: a PyAudio input stream pushes PCM frames into a queue via a callback
- **Rolling buffer**: incoming chunks are appended into a fixed-size buffer (`CHUNK=2048`)
- **FFT + windowing**: a Hann window is applied, then an `rfft` produces the magnitude spectrum
- **Frequency range**: only **2–8 kHz** is visualized
- **Binning**: adjacent FFT bins are averaged into fewer bars
- **Normalization + gating**: bars are normalized to a reference level and gated
- **Rendering**: PyQtGraph `BarGraphItem` draws the bars; optional peak markers are overlaid

---

## Configuration notes

Key constants near the top of `main.py`:

- `CHUNK = 2048` (FFT/buffer size)
- `RATE = 44100` (sample rate)
- `FREQ_MIN = 2000`, `FREQ_MAX = 8000` (displayed range)
- `OVERLAP_FACTOR = 4` (stream buffer uses `CHUNK / OVERLAP_FACTOR` frames)
- `DRAW_TIME = 20` ms (UI update interval)
