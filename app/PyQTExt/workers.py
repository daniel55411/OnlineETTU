from PyQt5.QtCore import QRunnable, pyqtSlot, pyqtSignal, QObject
from app.PyQTExt.pixmapItems import *
import app.openStreetMap as osm


class TileWorker(QRunnable):
    def __init__(self,
                 cache: "osm.Cache",
                 tile: "QTile"):
        super().__init__()
        self.tile = tile
        self.cache = cache
        self.signal = Signal()

    @pyqtSlot()
    def run(self):
        self.cache.get_tile(self.tile)
        self.signal.finish.emit(self.tile)
        self.setAutoDelete(True)


class TransportWorker(QRunnable):
    def __init__(self, transport: "QTransport"):
        super().__init__()


class Signal(QObject):
    finish = pyqtSignal(object)
