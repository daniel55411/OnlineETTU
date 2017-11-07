class Bound:
    def __init__(self):
        self.tile = None
        self.tile_size = 256

    def reversed_range(self, rect: "QRect"):
        raise NotImplementedError()

    def minmax(self, arr: list):
        raise NotImplementedError()

    def set_tile(self, tile: "QTile"):
        self.tile = tile

    def tile_in_bound(self, rect: "QRect"):
        raise NotImplementedError()

    def range(self, rect: "QRect"):
        raise NotImplementedError()

    def get_cell(self, index: int) -> (int, int):
        raise NotImplementedError()

    def get_index_cell(self, index: int) -> (int, int):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()


class LeftBound(Bound):
    def __str__(self):
        return "Left Bound"

    def __init__(self):
        super().__init__()

    def reversed_range(self, rect: "QRect"):
        return range(int(self.tile.map_y), rect.top() + 1, -self.tile_size)

    def tile_in_bound(self, rect: "QRect"):
        return self.tile.map_x > rect.left() - self.tile_size

    def range(self, rect: "QRect"):
        return range(int(self.tile.map_y), rect.bottom() + 1, self.tile_size)

    def minmax(self, arr: list):
        return min(arr, key=lambda tile: tile.map_x)

    def get_cell(self, index: int):
        return self.tile.map_x - self.tile_size, index

    def get_index_cell(self, index: int):
        return self.tile.x - 1, self.tile.y + index


class RightBound(Bound):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Right Bound"

    def tile_in_bound(self, rect: "QRect"):
        return self.tile.map_x < rect.width() + self.tile_size

    def range(self, rect: "QRect"):
        return range(int(self.tile.map_y), rect.bottom() + 1, self.tile_size)

    def reversed_range(self, rect: "QRect"):
        return range(int(self.tile.map_y), rect.top() + 1, -self.tile_size)

    def minmax(self, arr: list):
        return max(arr, key=lambda tile: tile.map_x)

    def get_cell(self, index: int):
        return self.tile.map_x + self.tile_size, index

    def get_index_cell(self, index: int):
        return self.tile.x + 1, self.tile.y + index


class TopBound(Bound):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Top Bound"

    def tile_in_bound(self, rect: "QRect"):
        return self.tile.map_y > rect.top() - self.tile_size

    def range(self, rect: "QRect"):
        return range(int(self.tile.map_x), rect.right() + 1, self.tile_size)

    def reversed_range(self, rect: "QRect"):
        return range(int(self.tile.map_x), rect.left() + 1, -self.tile_size)

    def minmax(self, arr: list):
        return min(arr, key=lambda tile: tile.map_y)

    def get_cell(self, index: int):
        return index, self.tile.map_y - self.tile_size

    def get_index_cell(self, index: int):
        return self.tile.x + index, self.tile.y - 1


class BottomBound(Bound):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Bottom Bound"

    def tile_in_bound(self, rect: "QRect"):
        return self.tile.map_y < rect.height() + self.tile_size

    def range(self, rect: "QRect"):
        return range(int(self.tile.map_x), rect.right() + 1, self.tile_size)

    def reversed_range(self, rect: "QRect"):
        return range(int(self.tile.map_y), rect.top + 1, -self.tile_size)

    def minmax(self, arr: list):
        return max(arr, key=lambda tile: tile.map_y)

    def get_cell(self, index: int):
        return index, self.tile.map_y + self.tile_size

    def get_index_cell(self, index: int):
        return self.tile.x + index, self.tile.y + 1