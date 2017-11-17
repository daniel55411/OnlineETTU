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
from app.PyQTExt.painters import *


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
        self.redraw_flag = False
        self.chosen_trams = list(self.ettu.get_trams())
        self.chosen_trolleybuses = list(self.ettu.get_trolleybuses())
        self.delta = QPoint(0, 0)
        self.drag_start = None
        self.current_pos = None
        self.thread_pool = QThreadPool()
        self.tile_size = 256
        self.init_scene()

    def init_scene(self):
        self.scene = QGraphicsScene(self.tile_size,
                                    self.tile_size,
                                    self.geometry().width(),
                                    self.geometry().height(),
                                    self)
        self.setScene(self.scene)
        self.tile_painter = TilePainter(self.scene, self.cache, self.thread_pool)
        self.transport_painter = TransportPainter(self.scene)
        self.refresh()

    def init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(100)

    def refresh(self):
        # self.chosen_trams = list(self.ettu.get_trams())
        # self.chosen_trolleybuses = list(self.ettu.get_trolleybuses())
        if self.redraw_flag:
            rect = QRect(self.geometry().x() - self.tile_size,
                         self.geometry().y() - self.tile_size,
                         self.geometry().right() + self.tile_size,
                         self.geometry().bottom() + self.tile_size)
            self.tile_painter.redraw(self.delta, self.geometry(), rect)
            # self.transport_painter.redraw(self.geometry(),
            #                               self.chosen_trolleybuses + self.chosen_trams,
            #                               self.get_widget_coordinates)
        else:
            self.scene.clear()
            self.tile_painter.draw(self.geometry())
            # self.transport_painter.draw(self.geometry(),
            #                             self.chosen_trolleybuses + self.chosen_trams,
            #                             self.get_widget_coordinates)
        self.redraw_flag = False
        self.update()

    def get_widget_coordinates(self, transport: "ettu.Transport"):
        x, y = osm.Translator.deg2num(transport.latitude, transport.longitude, self.tile_painter.zoom)
        tile = self.find_drawn_tile(x, y)
        if tile is None:
            return
        latitude, longitude = osm.Translator.num2deg(tile.x, tile.y, self.tile_painter.zoom)
        dy = osm.Translator.get_distance((latitude, longitude), (transport.latitude, longitude))
        dx = osm.Translator.get_distance((latitude, longitude), (latitude, transport.longitude))
        resolution = osm.Translator.get_resolution(transport.latitude, self.tile_painter.zoom)
        map_dy, map_dx = dy / resolution, dx / resolution
        return tile.map_x + map_dx, tile.map_y + map_dy

    def find_drawn_tile(self, x: int, y: int):
        for tile in self.tile_painter.drawn:
            if tile.x == x and tile.y == y:
                return tile
        return None

    def mousePressEvent(self, event):
        self.drag_start = event.localPos()

    def mouseMoveEvent(self, event):
        self.current_pos = event.localPos()
        tile = self.find_tile_by_map_coordinates(self.current_pos.x(), self.current_pos.y())
        if tile is None:
            return
        delta = self.current_pos - self.drag_start
        new_x, new_y = tile.x + delta.x() / 256, tile.y + delta.y() / 256
        new_lat, new_lon = osm.Translator.num2deg(new_x, new_y, self.tile_painter.zoom)
        old_lat, old_lon = osm.Translator.num2deg(tile.x, tile.y, self.tile_painter.zoom)
        coordinates_delta = (new_lat - old_lat, new_lon - old_lon)
        self.tile_painter.latitude -= coordinates_delta[0]
        self.tile_painter.longitude -= coordinates_delta[1]
        self.drag_start = self.current_pos
        self.delta = delta
        self.redraw_flag = True
        self.refresh()

    def find_tile_by_map_coordinates(self, x: int, y: int):
        for tile in self.tile_painter.drawn:
            if tile.map_x <= x <= tile.map_x + self.tile_painter.tile_size and \
                                    tile.map_y <= y <= tile.map_y + self.tile_painter.tile_size:
                return tile
        return None
