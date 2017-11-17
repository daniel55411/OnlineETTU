import unittest

from app.PyQTExt.widget import QTile
from app.openStreetMap import Tile


class TileTests(unittest.TestCase):
    def testTilesEquals(self):
        tile1 = Tile(1, 1, 15)
        tile2 = Tile(1, 1, 15)
        tile3 = Tile(1, 2, 15)
        tile4 = Tile(1, 1, 12)
        self.assertEqual(tile1, tile2)
        self.assertNotEqual(tile1, tile3)
        self.assertNotEqual(tile1, tile4)

    def testTilesInSequences(self):
        tile1 = Tile(1, 1, 15)
        tile2 = Tile(3, 3, 15)
        seq = [Tile(1, 1, 15), Tile(1, 2, 15), Tile(2, 1, 15), Tile(2, 2, 15)]
        self.assertTrue(tile1 in seq)
        self.assertFalse(tile2 in seq)

    def testQTileEquals(self):
        tile1 = QTile(Tile(1, 1, 15))
        tile2 = QTile(Tile(1, 1, 15))
        tile3 = QTile(Tile(1, 2, 15))
        tile4 = QTile(Tile(1, 1, 12))
        self.assertEqual(tile1, tile2)
        self.assertNotEqual(tile1, tile3)
        self.assertNotEqual(tile1, tile4)

    def testQTilesInSequences(self):
        tile1 = QTile(Tile(1, 1, 15))
        tile2 = QTile(Tile(3, 3, 15))
        seq = [QTile(Tile(1, 1, 15)), QTile(Tile(1, 2, 15)),
               QTile(Tile(2, 1, 15)), QTile(Tile(2, 2, 15))]
        self.assertTrue(tile1 in seq)
        self.assertFalse(tile2 in seq)

    def testTileHashEquals(self):
        tile1 = Tile(1, 1, 15)
        tile2 = Tile(1, 1, 15)
        tile3 = Tile(1, 2, 15)
        tile4 = Tile(1, 1, 12)
        self.assertEqual(tile1.__hash__(), tile2.__hash__())
        self.assertNotEqual(tile1.__hash__(), tile3.__hash__())
        self.assertNotEqual(tile1.__hash__(), tile4.__hash__())

    def testTileInSet(self):
        tile1 = QTile(Tile(1, 1, 15))
        tile2 = QTile(Tile(3, 3, 15))
        seq = {QTile(Tile(1, 1, 15)), QTile(Tile(1, 2, 15)),
               QTile(Tile(2, 1, 15)), QTile(Tile(2, 2, 15))}
        self.assertTrue(tile1 in seq)
        self.assertFalse(tile2 in seq)