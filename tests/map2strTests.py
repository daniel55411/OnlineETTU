import unittest
from app.openStreetMap import map2str


class Map2strTests(unittest.TestCase):
    def testMap2StrWithPaths(self):
        @map2str
        def a(paths=[]):
            return paths

        res1 = a(paths=[1, 2, 3])
        res2 = a([1, '2', 3])
        self.assertSequenceEqual(['1', '2', '3'], res1)
        self.assertSequenceEqual(['1', '2', '3'], res2)

    def testMap2StrWithoutPaths(self):
        @map2str
        def a(c, d):
            return c, d

        res1 = a(2, 2)
        self.assertEqual((2, 2), res1)

    def testMap2StrManyArray(self):
        @map2str
        def a(ar1, ar2, ar3):
            return ar1, ar2, ar3

        res = a(1, [1, 2, 3], [4, 5, 6])
        self.assertSequenceEqual(['1', '2', '3'], res[1])
        self.assertSequenceEqual([4, 5, 6], res[2])
        self.assertEqual(1, res[0])
