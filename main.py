from analyzer import AudioAnalyzer
from pyqtgraph.Qt import QtWidgets
import platform

# CONFIG
config = {
    "CHUNK": 2048,
    "RATE": 44100,
    "FREQ_MIN": 2000,
    "FREQ_MAX": 8000,
    "OVERLAP_FACTOR": 4,
    "DRAW_TIME": 20
}

def makeDpiAware():
    if platform.system() != "Windows":
        return
    import ctypes
    if int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

if __name__ == "__main__":
    makeDpiAware()
    app = QtWidgets.QApplication([])
    analyzer = AudioAnalyzer(config=config)
    analyzer.show()
    QtWidgets.QApplication.processEvents()
    analyzer.centerOnPrimaryScreen()
    app.exec()