import app.openStreetMap as osm
from PyQt5.QtWidgets import QGraphicsPixmapItem
from app.ettu import Transport, TransportType
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QPixmap, QColor, QBrush


class AbstractPixmapItem(QGraphicsPixmapItem):
    def __init__(self, map_x=0, map_y=0, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        self.map_x = map_x
        self.map_y = map_y
        self.setPos(self.map_x, self.map_y)

    def shift(self, point: "QPointF"):
        self.map_x += point.x()
        self.map_y += point.y()
        self.setPos(self.map_x, self.map_y)


class QTile(osm.Tile, AbstractPixmapItem):
    def __init__(self, tile: "osm.Tile", map_x=0, map_y=0, parent=None):
        osm.Tile.__init__(self, tile.x, tile.y, tile.zoom)
        AbstractPixmapItem.__init__(self, map_x, map_y, parent)


class QTransport(Transport, AbstractPixmapItem):
    transport_type_color = {
        TransportType.TRAM: QColor(255, 0, 0),
        TransportType.TROLLEYBUS: QColor(0, 0, 255)
    }

    def __init__(self, transport: "Transport", map_x=0, map_y=0, parent=None):
        Transport.__init__(self,
                           transport.transport_id,
                           transport.route_id,
                           transport.latitude,
                           transport.longitude,
                           transport.transport_type)
        AbstractPixmapItem.__init__(self, map_x, map_y, parent)
        painter = QPainter(self)
        painter.setBrush(self.transport_type_color[self.transport_type])
        painter.drawEllipse(self.map_x, self.map_y, 10, 10)
        painter.drawText(self.map_x, self.y, self.route_id)
