import math

class Cartesian:

    def __init__(self, x, y):
        self.x = x
        self.y = y

class LatLng:

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng

    def get_latlng(self, x, y):
        return LatLng(self.lat + y/111300.0, self.lng + x/111300.0/math.cos(self.lat/180.0*math.pi))

    def get_xy(self, latlng):
        return Cartesian((latlng.lng - self.lng) * 111300.0 * math.cos(self.lat/180.0*math.pi), (latlng.lat - self.lat) * 111300.0)

    def get_distance(self,latlng):
        p = self.get_xy(latlng)
        return math.sqrt(p.x*p.x + p.y*p.y)
