from app.openStreetMap import Tile
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene
from app.ettu import Transport, TransportType
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QPixmap, QColor, QBrush


class QItem:
    def __init__(self, map_x=0, map_y=0):
        self.map_x = map_x
        self.map_y = map_y

    def shift(self, point: "QPointF"):
        self.map_x += point.x()
        self.map_y += point.y()


class QTile(Tile, QItem):
    def __init__(self, tile: "Tile", map_x=0, map_y=0):
        Tile.__init__(self, tile.x, tile.y, tile.zoom)
        QItem.__init__(self, map_x, map_y)


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
