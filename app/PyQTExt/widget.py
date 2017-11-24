from PyQt5.QtWidgets import (QMainWindow, QWidget, QCheckBox,
                             QDockWidget, QVBoxLayout, QGridLayout,
                             QLabel, QPushButton, QHBoxLayout,
                             QGraphicsPixmapItem, QGraphicsView,
                             QGraphicsScene, QFrame)

from PyQt5.QtCore import (Qt, QRect, QPoint, QRectF,
                          QThread, QObject, pyqtSignal,
                          pyqtSlot, QThreadPool, QRunnable,
                          QTimer)
from PyQt5.QtGui import QPainter, QPixmap, QColor, QBrush
from app import ettu, openStreetMap as osm
from app.PyQTExt.QItems import TransportContextMenu, StationContextMenu
from app.PyQTExt.painters import *
from app.ettu import TransportType


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.map = MapWidget()
        self.initUI()
        # self.createDockWidget()

    def initUI(self):
        widget = QWidget(self)
        self.button1 = QPushButton('-')
        self.button1.clicked.connect(self.map.zoom_out)
        self.button2 = QPushButton('+')
        self.button2.clicked.connect(self.map.zoom_in)
        self.button3 = QPushButton('Update')
        self.button3.clicked.connect(self.map.update)
        layout = QVBoxLayout(widget)
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        ## layout.addWidget(self.button3)
        layout.addWidget(self.map)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

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
    def __init__(self):
        super().__init__()
        self.ettu = ettu.Receiver()
        self.osm = osm.Receiver()
        self.clicked_object = None
        self.delta = QPoint(0, 0)
        self.drag_start = None
        self.current_pos = None;print(self.geometry());
	self.tile_painter = TilePainter(self.osm, self.geometry())
        self.tile_painter.osm.connect_update_rect(self.update_map)
        self.transport_painter = TransportPainter(self.ettu)
        self.station_painter = StationPainter(self.ettu)
        self.transport_painter.ettu.connect_update_rect(self.update_map)
        self.update()
        self.init_timer()

    def zoom_in(self):
        if self.tile_painter.zoom < 18:
            self.tile_painter.zoom += 1
            self.tile_painter.set_map_rect(self.geometry())
            self.clicked_object = None
            self.tile_painter.download()
            self.update()

    def zoom_out(self):
        if self.tile_painter.zoom > 0:
            self.tile_painter.zoom -= 1
            self.tile_painter.set_map_rect(self.geometry())
            self.clicked_object = None
            self.tile_painter.download()
            self.update()

    def init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_transports)
        self.timer.start(15000)

    def update_map(self, rect: "QRect"):
        self.update()

    def update_transports(self):
        self.transport_painter.download()
        if isinstance(self.clicked_object, TransportContextMenu):
            self.clicked_object = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        self.tile_painter.draw(painter)
        self.transport_painter.draw(painter, self.get_widget_coordinates)
        self.station_painter.draw(painter, self.get_widget_coordinates)
        if self.clicked_object is not None:
            self.clicked_object.draw(painter, self.ettu.last_station)
        self.draw_legend(painter)
        painter.end()

    def get_widget_coordinates(self, ettu_obj):
        x, y = osm.Translator.deg2num(ettu_obj.latitude, ettu_obj.longitude, self.tile_painter.zoom)
        tile = self.find_drawn_tile(x, y)
        if tile is None:
            return
        latitude, longitude = osm.Translator.num2deg(tile.x, tile.y, self.tile_painter.zoom)
        dy = osm.Translator.get_distance((latitude, longitude), (ettu_obj.latitude, longitude))
        dx = osm.Translator.get_distance((latitude, longitude), (latitude, ettu_obj.longitude))
        resolution = osm.Translator.get_resolution(ettu_obj.latitude, self.tile_painter.zoom)
        map_dy, map_dx = dy / resolution, dx / resolution
        return tile.map_x + map_dx, tile.map_y + map_dy

    def find_drawn_tile(self, x: int, y: int):
        for tile in self.tile_painter.drawn:
            if tile.x == x and tile.y == y:
                return tile
        return None

    def mousePressEvent(self, event):
        self.clicked_object = None
        self.drag_start = event.localPos()
        for ettu_obj in self.ettu.all_transports + self.ettu.all_stations:
            coord = self.get_widget_coordinates(ettu_obj)
            if coord is not None:
                rect = QRectF(*coord, 20, 20)
                rect.translate(-10, -10)
                if rect.contains(self.drag_start):
                    if isinstance(ettu_obj, Transport):
                        self.clicked_object = TransportContextMenu(ettu_obj, self.drag_start.x(), self.drag_start.y())
                    else:
                        self.clicked_object = StationContextMenu(ettu_obj, self.drag_start.x(), self.drag_start.y())
                        self.ettu.get_arrive_time(ettu_obj.station_id)
                    self.update()

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
        self.tile_painter.set_map_rect(self.geometry())
        self.tile_painter.download()
        self.update()

    def find_tile_by_map_coordinates(self, x: int, y: int):
        for tile in self.tile_painter.drawn:
            if tile.map_x <= x <= tile.map_x + self.tile_painter.tile_size and \
                                    tile.map_y <= y <= tile.map_y + self.tile_painter.tile_size:
                return tile
        return None

    def draw_legend(self, painter: "QPainter"):
        painter.setBrush(QColor(255, 255, 255))
        width = 400
        height = 200
        rect = QRect(self.geometry().right() - width, self.geometry().bottom() - height, width ,height)
        painter.drawRect(rect)
        painter.setBrush(QTransport.transport_type_color[TransportType.TRAM])
        painter.drawEllipse(rect.x() + 10, rect.y() + 20, 10, 10)
        painter.drawText(rect.x() + 25, rect.y() + 25, 'Трамвай')
        painter.drawText(rect.x() + 25, rect.y() + 45, 'Тролейбус')
        painter.drawText(rect.x() + 25, rect.y() + 75, 'Остановка')
        painter.setBrush(QTransport.transport_type_color[TransportType.TROLLEYBUS])
        painter.drawEllipse(rect.x() + 10, rect.y() + 40, 10, 10)
        painter.setBrush(QStation.color)
        painter.drawEllipse(rect.x() + 10, rect.y() + 70, 10, 10)
