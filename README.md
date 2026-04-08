# Audio-Visualisation-Interface

A real-time audio visualisation tool written in Python. It captures a live audio stream from the system's default input device using **PyAudio** and renders an interactive waveform/spectrum display using **PyQtGraph**.

---

## Features

- **Real-time audio capture** from the system's default microphone or input device
- **Live waveform visualisation** rendered with PyQtGraph
- **Low-latency streaming** via PyAudio
- Lightweight and runs entirely on your local machine — no audio files required

---

## Requirements

| Dependency | Version |
|---|---|
| Python | ≥ 3.7 |
| [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) | ≥ 0.2.11 |
| [PyQtGraph](https://www.pyqtgraph.org/) | ≥ 0.12 |
| [PyQt5](https://pypi.org/project/PyQt5/) or [PySide2](https://pypi.org/project/PySide2/) | latest |
| [NumPy](https://numpy.org/) | ≥ 1.20 |

> **Note (macOS / Linux):** PyAudio depends on PortAudio. Install it first:
> - macOS: `brew install portaudio`
> - Ubuntu/Debian: `sudo apt-get install portaudio19-dev`

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/leobarth/Audio-Visualisation-Interface.git
   cd Audio-Visualisation-Interface
   ```

2. **Create and activate a virtual environment** *(recommended)*

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install pyaudio pyqtgraph PyQt5 numpy
   ```

---

## Usage

Run the main script to start the visualiser:

```bash
python main.py
```

The application window will open and immediately begin displaying the live audio waveform captured from your default input device.

---

## How It Works

1. **Audio capture** — PyAudio opens a stream on the system's default input device and reads chunks of raw PCM samples at a configurable sample rate (e.g. 44100 Hz).
2. **Signal processing** — The raw byte data is converted to a NumPy array for fast numerical operations.
3. **Visualisation** — PyQtGraph plots the samples in real time inside a Qt application window. The plot is updated on every new audio chunk, giving a smooth live display.

---

## Configuration

You can adjust the following constants at the top of `main.py` to tune performance and appearance:

| Parameter | Description | Default |
|---|---|---|
| `RATE` | Sample rate in Hz | `44100` |
| `CHUNK` | Number of frames per buffer | `1024` |
| `CHANNELS` | Number of input channels | `1` |
| `FORMAT` | PyAudio sample format | `pyaudio.paInt16` |

---

## Troubleshooting

- **No audio device found** — Make sure a microphone or line-in is connected and set as the default input device in your OS sound settings.
- **PyAudio installation fails** — Ensure PortAudio is installed (see [Requirements](#requirements)).
- **Blank / frozen plot** — Try increasing the `CHUNK` size or lowering the `RATE`.

---

## License

This project is open source. Feel free to use, modify, and distribute it.
