from PyQt5.QtCore import QRunnable, pyqtSlot, pyqtSignal, QObject
import app.PyQTExt.pixmapItems
import app.openStreetMap as osm


class TileWorker(QRunnable):
    def __init__(self,
                 cache: "osm.Cache",
                 tile: "app.PyQTExt.pixmapItems.QTile"):
        super().__init__()
        self.tile = tile
        self.cache = cache
        self.signal = TileSignal()

    @pyqtSlot()
    def run(self):
        self.cache.get_tile(self.tile)
        self.signal.finish.emit(self.tile)
        self.setAutoDelete(True)


class TileSignal(QObject):
    finish = pyqtSignal(object)
