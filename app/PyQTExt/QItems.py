from app.openStreetMap import Tile
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene
from app.ettu import Transport, TransportType, Station
from PyQt5.QtCore import QPointF, QRect, QPoint
from PyQt5.QtGui import QPainter, QPixmap, QColor, QBrush


class QItem:
    def __init__(self, map_x=0, map_y=0):
        self.map_x = map_x
        self.map_y = map_y

    def shift(self, point: "QPointF"):
        self.map_x += point.x()
        self.map_y += point.y()

    def draw(self, *args, **kwargs):
        raise NotImplementedError()


class QTile(Tile, QItem):
    def __init__(self, tile: "Tile", map_x=0, map_y=0):
        Tile.__init__(self, tile.x, tile.y, tile.zoom)
        QItem.__init__(self, map_x, map_y)

    def draw(self, painter: "QPainter", rect):
        pass


class QTransport(Transport, QItem):
    transport_type_color = {
        TransportType.TRAM: QColor(255, 0, 0),
        TransportType.TROLLEYBUS: QColor(0, 0, 255)
    }

    def __init__(self, transport: "Transport", map_x=0, map_y=0):
        Transport.__init__(self,
                           latitude=transport.latitude,
                           longitude=transport.longitude,
                           route_id=transport.route_id,
                           transport_id=transport.transport_id,
                           transport_type=transport.transport_type)
        QItem.__init__(self, map_x, map_y)

    def draw(self, painter: "QPainter"):
        painter.setBrush(self.transport_type_color[self.transport_type])
        painter.drawEllipse(self.map_x, self.map_y, 10, 10)
        painter.drawText(self.map_x, self.map_y, self.route_id)


class QStation(Station, QItem):
    color = QColor(255, 255, 255)

    def __init__(self, station: "Station", map_x=0, map_y=0):
        Station.__init__(self,
                         station_id=station.station_id,
                         name=station.name,
                         direction=station.direction,
                         latitude=station.latitude,
                         longitude=station.longitude,
                         transport_type=station.transport_type)
        QItem.__init__(self, map_x, map_y)

    def draw(self, painter: "QPainter"):
        painter.setBrush(self.color)
        painter.drawEllipse(self.map_x, self.map_y, 10, 10)
        # painter.drawText(self.ma)


class QContextMenu:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.width = 400
        self.height = 100
        self.background = QColor(253, 250, 211)

    def draw(self, *args, **kwargs):
        raise NotImplementedError

    def draw_loading(self, painter: "QPainter"):
        painter.setBrush(self.background)
        painter.drawRect(QRect(self.x, self.y, self.width, self.height))
        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(QPoint(self.x + 10, self.y + 75), "Loading...")



class TransportContextMenu(QContextMenu):
    transport_text = {
        TransportType.TRAM: "Трамвай",
        TransportType.TROLLEYBUS: "Троллейбус",
    }

    def __init__(self, transport: "Transport", x: int = 0, y: int = 0):
        super().__init__(x, y)
        self.transport = transport
        self.width = 160
        self.height = 40

    def draw(self, painter: "QPainter", data):
        painter.setBrush(self.background)
        painter.drawRect(QRect(self.x, self.y, self.width, self.height))
        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)
        text = "{}: №{}".format(self.transport_text[self.transport.transport_type], self.transport.route_id)
        painter.drawText(QPoint(self.x + 10, self.y + 25), text)

    def draw_loading(self, painter: "QPainter"):
        self.draw(painter, None)


class StationContextMenu(QContextMenu):
    def __init__(self, station: "Station", x: int = 0, y: int = 0):
        super().__init__(x, y)
        self.station = station

    def draw(self, painter: "QPainter", data: dict = None):
        if data is not None and self.station.station_id == data['id']:
            self.height = 100 + 15 * len(data['data'])
            self.width = 400
            painter.setBrush(self.background)
            painter.drawRect(QRect(self.x, self.y, self.width, self.height))
            font = painter.font()
            font.setPointSize(14)
            painter.setFont(font)
            text = "{} ({})".format(self.station.name, self.station.direction)
            painter.drawText(self.x + 10, self.y + 25, text)
            painter.drawText(self.x + 10, self.y + 45, '№\tВремя\tРасстояние')
            for index, d in enumerate(data['data']):
                text = '\t'.join(d)
                painter.drawText(self.x + 10, self.y + 65 + 20 * index, text)
        else:
            self.draw_loading(painter)

    def draw_loading(self, painter: "QPainter"):
        super().draw_loading(painter)
        text = "{} ({})".format(self.station.name, self.station.direction)
        painter.drawText(self.x + 10, self.y + 25, text )