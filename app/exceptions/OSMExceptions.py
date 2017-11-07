class OSMException(Exception):
    pass


class OSMTileNotSavedException(OSMException):
    def __str__(self):
        return 'Tile was not saved'
