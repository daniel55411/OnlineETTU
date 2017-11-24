from enum import Enum
import requests
import re
import json
from PyQt5.QtCore import QObject, pyqtSignal, QUrl, QPoint, QRect
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest


class Signal(QObject):
    signal = pyqtSignal(object)


class TransportType(Enum):
    TRAM = 1
    TROLLEYBUS = 2


class Receiver:
    url_routes = 'http://www.ettu.ru/pass/routes/'
    ettu_pattern_receiver = 'http://online.ettu.ru/map/getTrams/?p={},1,{}'
    prefix = {
        TransportType.TRAM: 'tm',
        TransportType.TROLLEYBUS: 'tl'
    }
    str_type = {
        TransportType.TRAM: 'tram',
        TransportType.TROLLEYBUS: 'troll'
    }
    route_re_pattern = r'/pass/routes/{}(?P<route>\d+)/'
    stations_pattern = 'http://map.ettu.ru/api/v2/{}/points/?apiKey=111'
    time_arrive_pattern = 'http://m.ettu.ru/station/{}'
    time_arrive_re_pattern = re.compile(r'<b>(?P<route>\d+)<\/b><\/div>\s+<div.*?>(?P<time>\d+ мин)<\/div>\s+<div.*?>(?P<dist>\d+ м)<\/div>')

    def __init__(self):
        self.__manager = QNetworkAccessManager()
        self.__update_signal = Signal()
        self.connect_handle_data(self.handle_network_data)
        self.trams = self.get_all_routes(TransportType.TRAM)
        self.trolleybuses = self.get_all_routes(TransportType.TROLLEYBUS)
        self.all_transports = []
        self.all_stations = []
        self.last_station = None

    def connect_handle_data(self, f):
        self.__manager.finished.connect(f)

    def connect_update_rect(self, f):
        self.__update_signal.signal.connect(f)

    def handle_network_data(self, reply):
        class_type, type_or_id = reply.request().attribute(QNetworkRequest.User)
        reply_routes = []
        reply_stations = []
        if not reply.error():
            data = reply.readAll()
            if class_type == Transport:
                reply_routes = json.loads(data.data().decode('utf-8-sig'))['T']
            elif class_type == Station:
                reply_stations = json.loads(data.data().decode('utf-8-sig'))['points']
            elif class_type == int:
                self.last_station = self.parse_arrive_time(data.data().decode(), type_or_id)
        reply.deleteLater()
        for info in reply_routes:
            self.all_transports.append(Transport(info[0], info[1], info[3], info[4], type_or_id))
        for info in reply_stations:
            if info['NAME'] != '':
                self.all_stations.append(Station(info['ID'], info['NAME'],
                                                 info['DIRECTION'], info['LAT'],
                                                 info['LON'], type_or_id))
        self.__update_signal.signal.emit(QRect())

    def parse_arrive_time(self, data: str, station_id: int):
        return {
            'id': station_id,
            'data': self.time_arrive_re_pattern.findall(data)
            }

    def get_trams(self):
        for route in self.trams:
            self.get_transports(TransportType.TRAM, route)

    def get_tram_stations(self):
        self.get_stations(TransportType.TRAM)

    def get_troll_stations(self):
        self.get_stations(TransportType.TROLLEYBUS)

    def get_trolleybuses(self):
        for route in self.trolleybuses:
            self.get_transports(TransportType.TROLLEYBUS, route)

    def get_all_routes(self, transport_type: "TransportType"):
        r = requests.get(self.url_routes)
        return re.findall(pattern=self.route_re_pattern.format(self.prefix[transport_type]),
                          string=r.text)

    def get_transports(self, transport_type, route):
        self.__url = QUrl(self.ettu_pattern_receiver.format(transport_type.value, route))
        request = QNetworkRequest()
        request.setUrl(self.__url)
        request.setAttribute(QNetworkRequest.User, (Transport, transport_type))
        self.__manager.get(request)

    def get_stations(self, transport_type):
        self.__url = QUrl(self.stations_pattern.format(self.str_type[transport_type]))
        request = QNetworkRequest()
        request.setUrl(self.__url)
        request.setAttribute(QNetworkRequest.User, (Station, transport_type))
        self.__manager.get(request)

    def get_arrive_time(self, station_id: int):
        self.__url = QUrl(self.time_arrive_pattern.format(station_id))
        request = QNetworkRequest()
        request.setUrl(self.__url)
        request.setAttribute(QNetworkRequest.User, (int, station_id))
        self.__manager.get(request)


class Transport:
    def __init__(self, transport_id, route_id, latitude, longitude, transport_type):
        self.transport_id = transport_id
        self.route_id = route_id
        self.longitude = longitude
        self.latitude = latitude
        self.transport_type = transport_type

    def is_tram(self):
        return self.transport_type == TransportType.TRAM


class Station:
    def __init__(self, station_id, name, direction, latitude, longitude, transport_type):
        self.station_id = station_id
        self.name = name
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.transport_type = transport_type
        self.direction = direction


if __name__ == "__main__":
    receiver = Receiver()
    print(receiver.trams)
