## Installation

1. **Create a virtual environment**

   ```bash
   # macOS / Linux
   python3 -m venv venv

   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   
   # Windows (Standard Command Prompt)
   venv\Scripts\activate
   ```

2. **Install system-level audio dependency (PortAudio)** *(required for PyAudio)*

   - **macOS (Homebrew)**:
   ```bash
   brew install portaudio
   ```
   - **Ubuntu / Debian**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y portaudio19-dev
   ```
   - **Windows**:
   Usually no extra system dependency is required (PyAudio is typically installed from a wheel). If `pip install -r requirements.txt` fails, upgrade packaging tools first:
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   ```

3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. *(Optional)* **Use a different Qt binding**

   This project uses **PyQt5** by default (as listed in `requirements.txt`). If you prefer **PySide2**, install it instead:

   ```bash
   pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5_sip
   pip install PySide2
   ```