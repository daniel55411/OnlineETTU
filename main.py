from PyQt5.QtWidgets import QApplication

from app.PyQTExt.widget import MainWindow

if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.showMaximized()
    app.exec_()
