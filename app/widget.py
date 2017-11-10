from _mysql import connect

from PyQt5.QtWidgets import QMainWindow, QWidget, QCheckBox, \
    QDockWidget, QVBoxLayout, QGridLayout, \
    QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QRect, QPoint, \
    QThread, QObject, pyqtSignal, \
    pyqtSlot, QThreadPool, QRunnable, \
    QTimer
from PyQt5.QtGui import QPainter, QPixmap, QColor
from app import ettu, openStreetMap as osm
from collections import deque


class QTile(osm.Tile):
    def __init__(self, tile: "osm.Tile", map_x=0, map_y=0):
        super().__init__(tile.x, tile.y, tile.zoom)
        self.map_x = map_x
        self.map_y = map_y
        self.corner = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.map = MapWidget()
        self.initUI()
        # self.createDockWidget()

    def initUI(self):
        widget = QWidget(self)
        self.button1 = QPushButton('-')
        self.button1.clicked.connect(self.dec_zoom)
        self.button2 = QPushButton('+')
        self.button2.clicked.connect(self.inc_zoom)
        self.button3 = QPushButton('Update')
        self.button3.clicked.connect(self.map.update)
        layout = QVBoxLayout(widget)
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.map)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # self.setCentralWidget(self.map)

    def inc_zoom(self):
        if self.map.zoom < 18:
            self.map.zoom += 1
            self.map.update()

    def dec_zoom(self):
        if self.map.zoom > 0:
            self.map.zoom -= 1
            self.map.update()

    def createDockWidget(self):
        self.docked = QDockWidget("Dockable", self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.docked)
        self.dockedWidget = ChooseRoutesWidget([1, 2, 3])
        self.docked.setWidget(self.dockedWidget)
        self.dockedWidget.setLayout(QVBoxLayout())


class DockWidget(QWidget):
    def __init__(self):
        super().__init__()


class ChooseRoutesWidget(QWidget):
    def __init__(self, routes: list):
        super().__init__()
        self.checkboxes = []
        self.routes = routes
        self.initUI()

    def initUI(self):
        self.layout = QGridLayout()
        for index, value in enumerate(self.routes):
            widget = QWidget()
            layout = QGridLayout()
            label = QLabel(str(value))
            layout.addWidget(label, 0, 0)
            checkbox = QCheckBox()
            layout.addWidget(checkbox, 0, 1)
            self.checkboxes.append(widget)
            widget.setLayout(layout)
            self.layout.addWidget(widget, index, 0)
        self.layout.setRowStretch(1)
        self.setLayout(self.layout)


class MapWidget(QWidget):
    transport_type_color = {
        ettu.TransportType.TRAM: QColor(255, 0, 0),
        ettu.TransportType.TROLLEYBUS: QColor(0, 0, 255)
    }

    def __init__(self):
        super().__init__()
        self.ettu = ettu.Receiver()
        self.cache = osm.Cache()
        self.tile_size = 256
        self.latitude = 56.86738408969649
        self.longitude = 60.532554388046265
        self.zoom = 14
        self.redraw_flag = False
        self.drawn_tiles = []
        self.chosen_trams = list(self.ettu.get_trams())
        self.chosen_trolleybuses = list(self.ettu.get_trolleybuses())
        self.delta = QPoint(0, 0)
        self.drag_start = None
        self.current_pos = None
        self.thread_pool = QThreadPool()
        self.queue = deque()
        self.flag_draw_tile = False

    def init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def paintEvent(self, event):
        painter = QPainter()
        # self.chosen_trams = list(self.ettu.get_trams())
        # self.chosen_trolleybuses = list(self.ettu.get_trolleybuses())
        painter.begin(self)
        if self.redraw_flag:
            self.redraw_tiles(painter)
        else:
            self.drawn_tiles.clear()
            self.draw_tiles(painter)
        self.draw_transports(painter)
        self.redraw_flag = False
        painter.end()

    @pyqtSlot(QPainter, osm.Tile, QRect, QRect)
    def _draw_tile(self, painter: "QPainter", tile: "osm.Tile", target: "QRect", source: "QRect"):
        self.flag_draw_tile = True
        self.queue.append(QTile(tile, map_x=target.x(), map_y=target.y()))
        self.update()
        self.flag_draw_tile = False

    def _draw_tile_(self, painter: "QPainter", tile: "osm.Tile", row: int, column: int):
        target = QRect(row, column, self.tile_size, self.tile_size)
        source = QRect(0, 0, self.tile_size, self.tile_size)
        painter.drawPixmap(target, QPixmap(self.cache.get_tile(tile)), source)

    def draw_tile(self, painter: "QPainter", tile: "osm.Tile", row: int, column: int):
        target = QRect(row, column, self.tile_size, self.tile_size)
        source = QRect(0, 0, self.tile_size, self.tile_size)

        # region
        # worker = Worker(self.cache, painter, tile, target, source)
        # worker.signal.finish.connect(self._draw_tile)
        # self.thread_pool.start(worker)
        # end region

        painter.drawPixmap(target, QPixmap(self.cache.get_tile(tile)), source)

    def draw_tiles(self, painter: "QPainter"):
        x, y = osm.Translator.deg2num(self.latitude, self.longitude, self.zoom)
        for column_index, column in enumerate(range(self.geometry().left(),
                                                    self.geometry().right() + self.tile_size + 1,
                                                    self.tile_size)):
            for row_index, row in enumerate(range(self.geometry().top(),
                                                  self.geometry().bottom() + self.tile_size + 1,
                                                  self.tile_size)):
                tile = osm.Tile(x + column_index, y + row_index, self.zoom)
                self.draw_tile(painter, tile, column, row)
                self.add_tile(tile, column, row)

    def add_tile(self, tile: "osm.Tile", x: int, y: int):
        qtile = QTile(tile)
        qtile.map_x = x
        qtile.map_y = y
        self.drawn_tiles.append(qtile)

    def draw_transport(self, painter: "QPainter",
                       x: int,
                       y: int,
                       transport: "ettu.Transport"):
        painter.setBrush(self.transport_type_color[transport.transport_type])
        painter.drawEllipse(x, y, 10, 10)
        painter.drawText(x, y, transport.route_id)

    def draw_transports(self, painter: "QPainter"):
        for tr in self.chosen_trams + self.chosen_trolleybuses:
            coordinates = self.get_widget_coordinates(tr)
            if coordinates is not None and self.geometry().contains(QPoint(*coordinates)):
                self.draw_transport(painter, *coordinates, tr)

    def get_widget_coordinates(self, transport: "ettu.Transport"):
        x, y = osm.Translator.deg2num(transport.latitude, transport.longitude, self.zoom)
        tile = self.find_drawn_tile(x, y)
        if tile is None:
            return
        latitude, longitude = osm.Translator.num2deg(tile.x, tile.y, self.zoom)
        dy = osm.Translator.get_distance((latitude, longitude), (transport.latitude, longitude))
        dx = osm.Translator.get_distance((latitude, longitude), (latitude, transport.longitude))
        resolution = osm.Translator.get_resolution(transport.latitude, self.zoom)
        map_dy, map_dx = dy / resolution, dx / resolution
        return tile.map_x + map_dx, tile.map_y + map_dy

    def find_drawn_tile(self, x: int, y: int):
        for tile in self.drawn_tiles:
            if tile.x == x and tile.y == y:
                return tile
        return None

    def redraw_tiles(self, painter: "QPainter"):
        for tile in self.drawn_tiles:
            tile.map_x += self.delta.x()
            tile.map_y += self.delta.y()
            self.draw_tile(painter, tile, tile.map_x, tile.map_y)
        self.remove_outside_tiles()
        self.draw_empty_tile(painter)

    def remove_outside_tiles(self):
        bounds = QRect(0, 0, self.geometry().width() + self.tile_size, self.geometry().height() + self.tile_size)
        bad_tiles = []
        for tile in self.drawn_tiles:
            if not bounds.intersects(QRect(tile.map_x, tile.map_y, self.tile_size, self.tile_size)):
                bad_tiles.append(tile)
        for tile in bad_tiles:
            self.drawn_tiles.remove(tile)

    def mousePressEvent(self, event):
        self.drag_start = event.localPos()

    def mouseMoveEvent(self, event):
        self.current_pos = event.localPos()
        tile = self.find_tile_by_map_coordinates(self.current_pos.x(), self.current_pos.y())
        if tile is None:
            return
        delta = self.current_pos - self.drag_start
        new_x, new_y = tile.x + delta.x() / 256, tile.y + delta.y() / 256
        new_lat, new_lon = osm.Translator.num2deg(new_x, new_y, self.zoom)
        old_lat, old_lon = osm.Translator.num2deg(tile.x, tile.y, self.zoom)
        coordinates_delta = (new_lat - old_lat, new_lon - old_lon)
        self.latitude -= coordinates_delta[0]
        self.longitude -= coordinates_delta[1]
        self.drag_start = self.current_pos
        self.delta = delta
        self.redraw_flag = True
        self.update()

    def find_tile_by_map_coordinates(self, x: int, y: int):
        for tile in self.drawn_tiles:
            if tile.map_x <= x <= tile.map_x + self.tile_size and \
                                    tile.map_y <= y <= tile.map_y + self.tile_size:
                return tile
        return None

    def draw_empty_tile(self, painter: "QPainter"):
        rect = QRect(self.geometry().x() - self.tile_size,
                     self.geometry().y() - self.tile_size,
                     self.geometry().width() + 2 * self.tile_size,
                     self.geometry().height() + 2 * self.tile_size)
        tile = self.drawn_tiles[0]
        visited = set()
        visited.add(tile)
        queue = deque()
        queue.append(tile)
        while len(queue) != 0:
            tile = queue.popleft()
            if not rect.contains(QPoint(tile.map_x, tile.map_y)):
                continue
            if tile not in self.drawn_tiles:
                self.draw_tile(painter, tile, tile.map_x, tile.map_y)
                self.add_tile(tile, tile.map_x, tile.map_y)
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if x == 0 and y == 0:
                        continue
                    n_tile = QTile(osm.Tile(tile.x + x, tile.y + y, self.zoom),
                                   tile.map_x + x * self.tile_size,
                                   tile.map_y + y * self.tile_size)
                    if n_tile not in visited:
                        queue.append(n_tile)
                        visited.add(n_tile)


class Worker(QRunnable):
    def __init__(self, cache: "osm.Cache",
                 painter: "QPainter",
                 tile: "osm.Tile",
                 target: QRect,
                 source: QRect):
        super().__init__()
        self.tile = tile
        self.cache = cache
        self.painter = painter
        self.target = target
        self.source = source
        self.signal = Signal()

    @pyqtSlot()
    def run(self):
        self.cache.get_tile(self.tile)
        self.signal.finish.emit(self.painter, self.tile, self.target, self.source)
        self.setAutoDelete(True)


class Signal(QObject):
    finish = pyqtSignal(QPainter, osm.Tile, QRect, QRect)
