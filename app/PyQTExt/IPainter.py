from app.PyQTExt.workers import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsScene
from app.PyQTExt.pixmapItems import QTile, QTransport
from app.openStreetMap import Cache
from PyQt5.QtCore import pyqtSlot, QThreadPool, QPointF, QRect, QPoint
from collections import deque
from app.ettu import Transport


class IPainter:
    def __init__(self, scene: "QGraphicsScene"):
        self.scene = scene
        self.drawn = []

    def draw(self, *args, **kwargs):
        raise NotImplementedError()

    def redraw(self, *args, **kwargs):
        raise NotImplementedError()


class TilePainter(IPainter):
    def __init__(self, scene: "QGraphicsScene", cache: "Cache", pool: "QThreadPool", zoom: int):
        super().__init__(scene)
        self.tile_size = 256
        self.cache = cache
        self.thread_pool = pool
        self.zoom = zoom

    def draw(self, tile: "QTile"):
        tile.setPixmap(QPixmap(self.cache.get_tile(tile)))
        tile.setZValue(-1)
        self.scene.addItem(tile)
        self.drawn.append(tile)

    def redraw(self, delta: "QPointF", bounds: "QRect", rect: "QRect"):
        for tile in self.drawn:
            tile.shift(delta)
        self.remove_outside_tiles(bounds)
        self.draw_empty_tile(rect)

    def remove_outside_tiles(self, bounds: "QRect"):
        bad_tiles = []
        for tile in self.drawn:
            if not bounds.intersects(QRect(tile.map_x, tile.map_y, self.tile_size, self.tile_size)):
                bad_tiles.append(tile)
        for tile in bad_tiles:
            self.drawn.remove(tile)

    def draw_empty_tile(self, rect: "QRect"):
        tile = self.drawn[0]
        visited = set()
        visited.add(tile)
        queue = deque()
        queue.append(tile)
        while len(queue) != 0:
            tile = queue.popleft()
            if not rect.contains(QPoint(tile.map_x, tile.map_y)):
                continue
            if tile not in self.drawn:
                self.draw(tile)
                self.drawn.append(tile)
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


class TransportPainter(IPainter):
    def __init__(self, scene: "QGraphicsScene"):
        super().__init__(scene)

    def redraw(self, *args, **kwargs):
        pass

    def draw(self, transport: "QTransport"):
        self.scene.addItem(transport)
