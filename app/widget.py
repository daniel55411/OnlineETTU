from PyQt5.QtWidgets import QMainWindow, QWidget, QCheckBox, \
    QDockWidget, QVBoxLayout, QGridLayout, \
    QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QRect, QPointF, QRectF, QPoint
from PyQt5.QtGui import QPainter, QPixmap, QColor
from app import ettu, openStreetMap as osm
from collections import deque

from app.classes import *


class QTile(osm.Tile):
    def __init__(self, tile: "osm.Tile", map_x=0, map_y=0):
        super().__init__(tile.x, tile.y, tile.zoom)
        self.map_x = map_x
        self.map_y = map_y
        self.corner = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        # self.createDockWidget()

    def initUI(self):
        self.setCentralWidget(MapWidget())

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
        self.zoom = 15
        self.redraw_flag = False
        self.drawn_tiles = []
        self.chosen_trams = list(self.ettu.get_trams())
        self.chosen_trolleybuses = []
        self.delta = QPoint(0, 0)
        self.drag_start = None
        self.current_pos = None

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        if self.redraw_flag:
            self.redraw_tiles(painter)
        else:
            self.draw_tiles(painter)
        self.draw_transports(painter)
        self.redraw_flag = False
        painter.end()

    def draw_tile(self, painter: "QPainter", tile: "osm.Tile", row: int, column: int):
        target = QRect(row, column, self.tile_size, self.tile_size)
        source = QRect(0, 0, self.tile_size, self.tile_size)
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
        latitude, longitude = osm.Translator.num2deg(tile.x, tile.y, tile.zoom)
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
        quque = deque()
        quque.append(tile)
        while len(quque) != 0:
            tile = quque.popleft()
            if not rect.contains(QPoint(tile.map_x, tile.map_y)):
                continue
            if tile not in self.drawn_tiles:
                self.draw_tile(painter, tile, tile.map_x, tile.map_y)
                self.add_tile(tile, tile.map_x, tile.map_y)
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if x == 0 and y == 0:
                        continue
                    n_tile = QTile(osm.Tile(tile.x + x, tile.y + y, tile.zoom),
                                   tile.map_x + x * self.tile_size,
                                   tile.map_y + y * self.tile_size)
                    if n_tile not in visited:
                        quque.append(n_tile)
                        visited.add(n_tile)
