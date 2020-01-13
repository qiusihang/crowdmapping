
import xml.dom.minidom
import latlng
from road import *
import matplotlib.pyplot as plt

class RoadNetwork:

    def __init__(self, xml_filename):
        self.roads = []
        self.aggregator = aggregator.Aggregator()

        DOMTree = xml.dom.minidom.parse(xml_filename)
        root = DOMTree.documentElement
        xml_roads = root.getElementsByTagName("road")
        i = 0
        for xml_road in xml_roads:
            coords = []
            nodes = xml_road.getElementsByTagName("node")
            for node in nodes:
                coords.append( latlng.LatLng(float(node.getAttribute('lat')),float(node.getAttribute('lng'))) )
            self.roads.append(Road(i,coords))
            i += 1

        for road in self.roads:
            cur_pos = LocInRoad(road,0,0)
            interval = road.distances[-1]/(int(road.distances[-1] / 50) + 1)+0.1
            while True:
                next_pos = road.get_pos_from_to(cur_pos, interval)
                if next_pos.tdis < 0:
                    uoa = UoA(road,cur_pos,LocInRoad(road,len(road.nodes)-1,0))
                    break
                else:
                    uoa = UoA(road,cur_pos,next_pos)
                    cur_pos = next_pos

    def plot_map(self, holdon = False):
        for road in self.roads:
            ndx = []
            ndy = []
            for node in road.nodes:
                ndy.append(node.lat)
                ndx.append(node.lng)
            plt.plot(ndx, ndy, lw = 0.5, c = [0.3,0.3,0.3])
            #plt.plot(ndx, ndy)
        if holdon == False: plt.show()

    def total_workload(self):
        s = 0
        for road in self.roads:
            l = len(road.nodes)
            for i in range(1,l):
                s += road.nodes[i-1].get_distance(road.nodes[i])
        return s

    def aggregate(self):
        self.aggregator.objects = []
        self.aggregator.weights = []
        for road in self.roads:
            for obj in road.aggregator.aggregated_objects:
                self.aggregator.add_object(obj.lat, obj.lng)
        self.aggregator.aggregate_using_treefinder()
