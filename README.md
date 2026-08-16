# Audio Analyzer (PyAudio + PyQtGraph)

A real-time **spectrum analyzer / audio visualiser** written in Python.

`main.py` captures audio from your system’s **default input device** using **PyAudio**, performs an FFT on a rolling buffer, and renders a **color-coded bar spectrum** in a **PyQtGraph** window. A control panel lets you tune calibration, gating, EQ, smoothing (“ballistics”), peak-hold, and gain in real time.


## Requirements

- Python 3
- PyAudio (PortAudio)
- NumPy
- PyQtGraph
- Qt bindings (PyQt5 recommended)
- This application is **Windows-optimized**! Please verify PyAudio and PyQt compatibility for other operating systems.


## Installation

```bash
git clone https://github.com/leobarth/Audio-Visualisation-Interface.git
cd Audio-Visualisation-Interface

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

> **Note (macOS / Linux):** PyAudio requires PortAudio
> - macOS: `brew install portaudio`
> - Ubuntu/Debian: `sudo apt install python3-pyaudio`

> Ensure these are installed correctly.


## Usage

Run:

```bash
python main.py
```

Close the window to save the current control values back to `settings.json`.
On the first run, default settings will be loaded.


## Configuration notes

Key constants near the top of `main.py`:

- `CHUNK = 2048` (FFT/buffer size)
- `RATE = 44100` (sample rate)
- `FREQ_MIN = 2000`, `FREQ_MAX = 8000` (displayed range)
- `OVERLAP_FACTOR = 4` (stream buffer uses `CHUNK / OVERLAP_FACTOR` frames)
- `DRAW_TIME = 20` ms (UI update interval)

**Only tweak these values if completely necessary.**


## Author

Leo Barth