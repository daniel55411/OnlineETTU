from app.PyQTExt.QItems import QTile, QTransport
from PyQt5.QtCore import QPointF, QRect, QPoint
from app.ettu import Transport
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
                tile = QTile(Tile(x, y, self.zoom), (x - self.map_rect.left()) * TILE_SIZE, (y - self.map_rect.top()) * TILE_SIZE)
                self.draw_tile(painter, tile)

    def set_map_rect(self, rect: "QRect"):
        x, y = Translator.deg2num(self.latitude, self.longitude, self.zoom)
        width = rect.width() // TILE_SIZE + 2
        height = rect.height() // TILE_SIZE + 2
        self.map_rect = QRect(x, y, width, height)

    def handle_network_data(self, reply):
        self.osm.handle_network_data(reply)
        self.osm.purge_cache(self.map_rect)
        self.download()

    def download(self):
        for x in range(self.map_rect.left(), self.map_rect.right()):
            for y in range(self.map_rect.top(), self.map_rect.bottom()):
                tile = Tile(x, y, self.zoom)
                if not self.osm.exist_tile((tile.x, tile.y)):
                    self.osm.download_tile(tile)
                    return


class TransportPainter(IPainter):
    def __init__(self):
        super().__init__()

    def redraw(self, rect: "QRect", collection: list, get_coordinates_function):
        self._draw(rect, collection, get_coordinates_function)

    def draw_one(self, transport: "QTransport"):
        if transport not in self.drawn:
            self.scene.addItem(transport)
            self.drawn.append(transport)

    def draw(self, rect: "QRect", collection: list, get_coordinates_function):
        self.drawn.clear()
        self._draw(rect, collection, get_coordinates_function)

    def _draw(self, rect: "QRect", collection: list, get_coordinates_function):
        for tr in collection:
            coordinates = get_coordinates_function(tr)
            if coordinates is not None and rect.contains(QPoint(*coordinates)):
                self.draw_transport(*coordinates, tr)

    def draw_transport(self, coordinates: tuple, transport: "Transport"):
        self.draw_one(QTransport(transport, *coordinates))
