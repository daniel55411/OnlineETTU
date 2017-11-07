import math
import os.path
import requests
from app.exceptions.OSMExceptions import *


def map2str(f):
    def g(*args, **kwargs):
        # print(args, kwargs)
        result = args
        if 'paths' in kwargs:
            kwargs['paths'] = list(map(str, kwargs['paths']))
        else:
            result = []
            flag = True
            for arg in args:
                if isinstance(arg, list) and flag:
                    result.append(list(map(str, arg)))
                    flag = False
                else:
                    result.append(arg)
        return f(*result, **kwargs)

    return g


class Receiver:
    server_pattern = 'http://a.tile2.opencyclemap.org/transport/{}/{}/{}.png'

    def get_tile_stream(self, zoom, xtile, ytile):
        r = requests.get(self.server_pattern.format(zoom, xtile, ytile))
        return r.content


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


class Cache:
    absolute_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(absolute_dir, 'cache')

    def __init__(self):
        if not self.exist():
            os.makedirs(self.cache_dir)
        self.receiver = Receiver()

    @map2str
    def exist(self, paths=[]):
        return os.path.exists(os.path.join(self.cache_dir, *paths))

    @map2str
    def get_name(self, name, paths=[]):
        return '{}/{}.png'.format(os.path.join(self.cache_dir, *paths), name)

    @map2str
    def create_subfolder(self, paths=[]):
        for index in range(1, len(paths) + 1):
            if not self.exist(paths[:index]):
                os.makedirs(os.path.join(self.cache_dir, *paths[:index]))

    def save(self, stream, tile: "Tile"):
        paths = [tile.zoom, tile.x]
        self.create_subfolder(paths=paths)
        with open(self.get_name(tile.y, paths), 'wb') as file:
            file.write(stream)

    def get_tile(self, tile: "Tile"):
        tile_path = self.get_name(tile.y, [tile.zoom, tile.x])
        if os.path.exists(tile_path):
            return tile_path
        else:
            self.save(self.receiver.get_tile_stream(tile.zoom, tile.x, tile.y), tile)
            if os.path.exists(tile_path):
                return tile_path

        raise OSMTileNotSavedException()


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
