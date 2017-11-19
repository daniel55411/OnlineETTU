import math
from app.exceptions.OSMExceptions import *
from threading import Lock
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkDiskCache
from PyQt5.QtCore import QUrl, QPoint, pyqtSignal, QRect, Qt, QObject, QStandardPaths
from PyQt5.QtGui import QImage, QPixmap

TILE_SIZE = 256


class Signal(QObject):
    signal = pyqtSignal(object)


class Receiver:
    server_pattern = 'http://a.tile2.opencyclemap.org/transport/{}/{}/{}.png'

    def __init__(self):
        self.__manager = QNetworkAccessManager()
        self.__cache = Cache()
        self.__update_signal = Signal()
        cache = QNetworkDiskCache()
        cache.setCacheDirectory(
            QStandardPaths.writableLocation(QStandardPaths.CacheLocation))
        self.__manager.setCache(cache)
        self.__url = QUrl()
        self.__visited = set()

    def connect_handle_data(self, f):
        self.__manager.finished.connect(f)

    def connect_update_rect(self, f):
        self.__update_signal.signal.connect(f)

    def download_tile(self, tile: "Tile"):
        self.__url = QUrl(self.server_pattern.format(tile.zoom, tile.x, tile.y))
        if (tile.x, tile.y) not in self.__visited:
            request = QNetworkRequest()
            request.setUrl(self.__url)
            request.setAttribute(QNetworkRequest.User, (tile.x, tile.y))
            self.__manager.get(request)
            self.__visited.add((tile.x, tile.y))

    def handle_network_data(self, reply):
        image = QImage()
        point = reply.request().attribute(QNetworkRequest.User)
        if not reply.error():
            if image.load(reply, None):
                self.__cache.save(point, QPixmap.fromImage(image))
        reply.deleteLater()
        self.__update_signal.signal.emit(QRect(*point, TILE_SIZE, TILE_SIZE))

    def get_tile(self, point: tuple):
        return self.__cache.get_tile_pixmap(point)

    def exist_tile(self, point: tuple):
        return self.__cache.exist(point)

    def purge_cache(self, rect: "QRect"):
        self.__cache.purge_unused_tiles(rect)
        bounds = rect.adjusted(-2, -2, 2, 2)
        for point in list(self.__visited):
            if not bounds.contains(QPoint(*point)):
                self.__visited.remove(point)


class Tile:
    def __init__(self, x, y, zoom):
        self.x = x
        self.y = y
        self.zoom = zoom

    def __eq__(self, other):
        assert isinstance(other, Tile)
        return self.x == other.x and \
               self.y == other.y and \
               self.zoom == other.zoom

    def __hash__(self):
        return 211 * 211 * self.x + 211 * self.y + self.zoom

    def __repr__(self):
        return "x: {}, y: {}, zoom: {}".format(self.x, self.y, self.zoom)


class Cache:
    def __init__(self):
        self.cache = {}
        self.empty_tile = QPixmap(TILE_SIZE, TILE_SIZE)
        self.empty_tile.fill(Qt.lightGray)

    def save(self, point: tuple, pixmap: "QPixmap"):
        self.cache[point] = pixmap

    def exist(self, point: tuple):
        return point in self.cache

    def get_tile_pixmap(self, point: tuple):
        if self.exist(point):
            return self.cache[point]
        else:
            return self.empty_tile

    def purge_unused_tiles(self, rect: "QRect"):
        bounds = rect.adjusted(-2, -2, 2, 2)
        for point in list(self.cache.keys()):
            if not bounds.contains(QPoint(*point)):
                del self.cache[point]


class Translator:
    @staticmethod
    def deg2num(lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return xtile, ytile

    @staticmethod
    def num2deg(xtile, ytile, zoom):
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return lat_deg, lon_deg

    @staticmethod
    def get_resolution(latitude, zoom):
        return 156543.03 * math.cos(math.radians(latitude)) / (2 ** zoom)

    @staticmethod
    def get_distance(point1: tuple, point2: tuple):
        r = 6371
        lat_1, lon_1 = point1
        lat_2, lon_2 = point2
        lat_rad = math.radians(lat_2 - lat_1)
        lon_rad = math.radians(lon_2 - lon_1)
        lat_1 = math.radians(lat_1)
        lat_2 = math.radians(lat_2)
        a = math.sin(lat_rad / 2) ** 2 + \
            math.sin(lon_rad / 2) ** 2 * math.cos(lat_1) * math.cos(lat_2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c * 1000
