from app.widget import MainWindow
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.showMaximized()
    app.exec_()
    # import sys
    # import time
    # from app.qtasync import AsyncTask, coroutine
    # from PyQt5 import QtGui
    # from PyQt5.QtCore import QThread
    # from PyQt5.QtWidgets import QMainWindow, QWidget, QCheckBox, \
    #     QDockWidget, QVBoxLayout, QGridLayout, \
    #     QLabel, QPushButton, QHBoxLayout
    # from PyQt5.QtCore import Qt, QRect, QPointF, QRectF, QPoint
    # from PyQt5.QtGui import QPainter, QPixmap, QColor
    # from app import ettu, openStreetMap as osm
    # from collections import deque
    #
    #
    # class MainWindow(QMainWindow):
    #     def __init__(self):
    #         super(MainWindow, self).__init__()
    #         self.initUI()
    #
    #     def initUI(self):
    #         self.cmd_button = QPushButton("Push", self)
    #         self.cmd_button.clicked.connect(self.send_evt)
    #         self.statusBar()
    #         self.show()
    #
    #     def worker(self, inval, s = 2):
    #         print("in worker, received '%s'" % inval)
    #         time.sleep(s)
    #         return "%s worked" % inval
    #
    #     @coroutine
    #     def send_evt(self, arg):
    #         out = AsyncTask(self.worker, "test string", 5)
    #         out2 = AsyncTask(self.worker, "another test string")
    #         QThread.sleep(3)
    #         print("kicked off async task, waiting for it to be done")
    #         # val = yield out
    #         print(1)
    #         print("out is %s" % (yield out))
    #         print('No dalay')
    #         print("out2 is %s" % (yield out2))
    #         out = yield AsyncTask(self.worker, "Some other string")
    #         print("out is %s" % out)
    #
    #
    # if __name__ == "__main__":
    #     app = QApplication(sys.argv)
    #     m = MainWindow()
    #     sys.exit(app.exec_())
