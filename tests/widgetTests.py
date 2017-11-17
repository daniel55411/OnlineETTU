import unittest

from app.PyQTExt.widget import MapWidget, QTile
from app.openStreetMap import Tile


class WidgetTests(unittest.TestCase):
    def testRemoveOutsideTiles(self):
        widget = MapWidget()
        for row in range(2):
            for column in range(2):
                qtile = QTile(Tile(0.0000, 0.0000, 15))
                qtile.map_x = column * 256
                qtile.map_y = row * 256
                widget.drawn_tiles.append(qtile)
