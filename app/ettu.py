from enum import Enum
import requests
import re


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
    route_re_pattern = r'/pass/routes/{}(?P<route>\d+)/'

    def __init__(self):
        self.trams = self.get_all_routes(TransportType.TRAM)
        self.trolleybuses = self.get_all_routes(TransportType.TROLLEYBUS)

    def get_trams(self):
        for route in self.trams:
            yield from self.get_transports(TransportType.TRAM, route)

    def get_trolleybuses(self):
        for route in self.trolleybuses:
            yield from self.get_transports(TransportType.TROLLEYBUS, route)

    def get_all_routes(self, transport_type: "TransportType"):
        r = requests.get(self.url_routes)
        return re.findall(pattern=self.route_re_pattern.format(self.prefix[transport_type]),
                          string=r.text)

    def get_transports(self, transport_type, route):
        r = requests.get(self.ettu_pattern_receiver.format(transport_type.value, route))
        if r.status_code != 200:
            return None
        data = r.json()['T']
        for info in data:
            yield Transport(info[0], info[1], info[3], info[4], transport_type)


class Transport:
    def __init__(self, transport_id, route_id, latitude, longitude, transport_type):
        self.transport_id = transport_id
        self.route_id = route_id
        self.longitude = longitude
        self.latitude = latitude
        self.transport_type = transport_type

    def is_tram(self):
        return self.transport_type == TransportType.TRAM


if __name__ == "__main__":
    receiver = Receiver()
    print(receiver.trams)

