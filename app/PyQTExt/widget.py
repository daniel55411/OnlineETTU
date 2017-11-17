from _mysql import connect

from PyQt5.QtWidgets import (QMainWindow, QWidget, QCheckBox,
                             QDockWidget, QVBoxLayout, QGridLayout,
                             QLabel, QPushButton, QHBoxLayout,
                             QGraphicsPixmapItem, QGraphicsView,
                             QGraphicsScene)

from PyQt5.QtCore import (Qt, QRect, QPoint, QRectF,
                          QThread, QObject, pyqtSignal,
                          pyqtSlot, QThreadPool, QRunnable,
                          QTimer)
from PyQt5.QtGui import QPainter, QPixmap, QColor, QBrush
from app import ettu, openStreetMap as osm
from collections import deque
from app.PyQTExt.pixmapItems import *
from app.PyQTExt.workers import *


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
        self.button3.clicked.connect(self.map.refresh)
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
            self.map.refresh()

    def dec_zoom(self):
        if self.map.zoom > 0:
            self.map.zoom -= 1
            self.map.refresh()

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


class MapWidget(QGraphicsView):
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
        self.paint_task = []
        self.init_scene()

    def init_scene(self):
        self.scene = QGraphicsScene(self.tile_size,
                                    self.tile_size,
                                    self.geometry().width(),
                                    self.geometry().height(),
                                    self)
        self.setScene(self.scene)
        self.refresh()

    def init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(100)

    def refresh(self):
        # self.chosen_trams = list(self.ettu.get_trams())
        # self.chosen_trolleybuses = list(self.ettu.get_trolleybuses())
        if self.redraw_flag:
            self.redraw_tiles()
        else:
            self.drawn_tiles.clear()
            self.scene.clear()
            self.draw_tiles()
        self.redraw_flag = False
        self.draw_transports()
        self.update()

    @pyqtSlot(object)
    def _draw_tile(self, tile: "QTile"):
        if tile.zoom == self.zoom:
            tile.setPixmap(QPixmap(self.cache.get_tile(tile)))
            tile.setZValue(-1)
            self.scene.addItem(tile)

    def draw_tile(self, tile: "QTile"):
        worker = TileWorker(self.cache, tile)
        worker.signal.finish.connect(self._draw_tile)
        self.thread_pool.start(worker)

    def draw_tiles(self):
        x, y = osm.Translator.deg2num(self.latitude, self.longitude, self.zoom)
        for column_index, column in enumerate(range(self.geometry().left() - 2*self.tile_size,
                                                    self.geometry().right() + 2*self.tile_size,
                                                    self.tile_size)):
            for row_index, row in enumerate(range(self.geometry().top() - 2*self.tile_size,
                                                  self.geometry().bottom() + 2*self.tile_size,
                                                  self.tile_size)):
                tile = QTile(
                    osm.Tile(x + column_index, y + row_index, self.zoom), column, row)
                self.draw_tile(tile)
                self.add_tile(tile)

    def add_tile(self, tile: "QTile"):
        self.drawn_tiles.append(tile)

    def draw_transport(self,
                       x: int,
                       y: int,
                       transport: "ettu.Transport"):
        self.scene.addEllipse(x, y, 10, 10,
                              brush=QBrush(QColor(self.transport_type_color[transport.transport_type])))
        item = self.scene.addText(transport.route_id)
        item.setPos(x, y)

    def draw_transports(self):
        for tr in self.chosen_trams + self.chosen_trolleybuses:
            coordinates = self.get_widget_coordinates(tr)
            if coordinates is not None and self.geometry().contains(QPoint(*coordinates)):
                self.draw_transport(*coordinates, tr)

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

    def redraw_tiles(self):
        for tile in self.drawn_tiles:
            tile.shift(self.delta)
        self.remove_outside_tiles()
        self.draw_empty_tile()

    def remove_outside_tiles(self):
        bounds = QRect(self.geometry().x() - self.tile_size,
                       self.geometry().y() - self.tile_size,
                       self.geometry().width() + self.tile_size,
                       self.geometry().height() + self.tile_size)
        bounds = self.geometry()
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
        self.refresh()

    def find_tile_by_map_coordinates(self, x: int, y: int):
        for tile in self.drawn_tiles:
            if tile.map_x <= x <= tile.map_x + self.tile_size and \
                                    tile.map_y <= y <= tile.map_y + self.tile_size:
                return tile
        return None

    def draw_empty_tile(self):
        rect = QRect(self.geometry().x() - self.tile_size,
                     self.geometry().y() - self.tile_size,
                     self.geometry().right() + self.tile_size,
                     self.geometry().bottom() + self.tile_size)
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
                self.draw_tile(tile)
                self.add_tile(tile)
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
