from PyQt5.QtGui import QPainter

from app.PyQTExt.QItems import QTile, QTransport, QStation
from PyQt5.QtCore import QPointF, QRect, QPoint
from app.ettu import Transport, Receiver
from app.openStreetMap import Tile, Translator

TILE_SIZE = 256


class IPainter:
    def __init__(self):
        self.drawn = []

    def draw(self, *args, **kwargs):
        raise NotImplementedError()


class TilePainter(IPainter):
    def __init__(self, osm: "osm.Receiver", screen: "QRect"):
        super().__init__()
        self.tile_size = TILE_SIZE
        self.osm = osm
        self.osm.connect_handle_data(self.handle_network_data)
        self.zoom = 14
        self.latitude = 56.86738408969649
        self.longitude = 60.532554388046265
        self.set_map_rect(screen)
        self.download()

    def draw_tile(self, painter: "QPainter", tile: "QTile"):
        if tile.zoom == self.zoom:
            self.drawn.append(tile)
            target = QRect(tile.map_x, tile.map_y, TILE_SIZE, TILE_SIZE)
            painter.drawPixmap(target, self.osm.get_tile((tile.x, tile.y)))

    def draw(self, painter: "QPainter"):
        for x in range(self.map_rect.left(), self.map_rect.right()):
            for y in range(self.map_rect.top(), self.map_rect.bottom()):
                tile = QTile(Tile(x, y, self.zoom), (x - self.map_rect.left()) * TILE_SIZE,
                             (y - self.map_rect.top()) * TILE_SIZE)
                self.draw_tile(painter, tile)

    def set_map_rect(self, rect: "QRect"):
        x, y = Translator.deg2num(self.latitude, self.longitude, self.zoom)
        width = rect.width() // TILE_SIZE + 2
        height = rect.height() // TILE_SIZE + 2
        self.map_rect = QRect(x, y, width, height)

    def handle_network_data(self, reply):
        self.osm.handle_network_data(reply)
        self.osm.purge_cache(self.map_rect)
        self.drawn = [tile for tile in self.drawn if self.osm.exist_tile((tile.x, tile.y))]
        self.download()

    def download(self):
        self.drawn.clear()
        for x in range(self.map_rect.left(), self.map_rect.right()):
            for y in range(self.map_rect.top(), self.map_rect.bottom()):
                tile = Tile(x, y, self.zoom)
                if not self.osm.exist_tile((tile.x, tile.y)):
                    self.osm.download_tile(tile)
                    return


class TransportPainter(IPainter):
    def __init__(self, ettu: "Receiver"):
        super().__init__()
        self.ettu = ettu
        self.download()

    def draw(self, painter: "QPainter", get_coordinates_function):
        for tr in self.ettu.all_transports:
            coordinates = get_coordinates_function(tr)
            if coordinates is not None:
                QTransport(tr, *coordinates).draw(painter)

    def download(self):
        self.ettu.all_transports.clear()
        self.ettu.get_trams()
        self.ettu.get_trolleybuses()


class StationPainter(IPainter):
    def __init__(self, ettu: "Receiver"):
        super().__init__()
        self.ettu = ettu
        self.download()

    def draw(self, painter: "QPainter", get_coordinates_function):
        for station in self.ettu.all_stations:
            coordinates = get_coordinates_function(station)
            if coordinates is not None:
                QStation(station, *coordinates).draw(painter)

    def download(self):
        self.ettu.all_stations.clear()
        self.ettu.get_tram_stations()
        self.ettu.get_troll_stations()

