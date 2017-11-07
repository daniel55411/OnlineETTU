from app.widget import MainWindow
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.showMaximized()
    app.exec_()
