
import latlng
import aggregator
import predictor
import matplotlib.pyplot as plt
import math

class Road:

    def __init__(self, ref, nodes):
        self.ref = ref
        self.nodes = nodes
        self.uoas = []
        self.aggregator = aggregator.Aggregator()
        self.predictor = predictor.Predictor(self)
        self.distances = [0]
        for i in range(1,len(nodes)): # len() is O(1)
            self.distances.append(self.distances[i-1]+nodes[i-1].get_distance(nodes[i]))
        self.length = self.distances[-1]

    def add_uoa(self, uoa):
        self.uoas.append(uoa)

    def get_pos_of(self, distance):
        return self.get_pos_from_to(LocInRoad(self,0,0), distance)

    def get_pos_from_to(self, cur_pos, distance): # distance means moving distance here
        if cur_pos.tdis + distance < 0:
            return LocInRoad(self,-1,0)
        if cur_pos.tdis + distance > self.distances[-1]:
            return LocInRoad(self,-1,0)
        if distance < 0:
            return self.get_pos_from_to(LocInRoad(self,0,0),cur_pos.tdis+distance)
        index = cur_pos.index
        dis = cur_pos.dis + distance
        l = len(self.nodes)
        for i in range(index+1, l):
            d = self.nodes[i-1].get_distance(self.nodes[i])
            if d >= dis:
                return LocInRoad(self, i-1, dis)
            dis -= d
        return LocInRoad(self,-1,0)

    def leftright(self, p1, p2, p3):
        # p1, p2 and p3 are Cartesian coordinates
        # to calculate if p1 is on the left side (-1) or right side (1) of the vector p2->p3
        v1 = latlng.Cartesian(p1.x - p2.x, p1.y - p2.y)
        v2 = latlng.Cartesian(p3.x - p2.x, p3.y - p2.y)
        s = v1.x * v2.y - v2.x * v1.y
        # left: -1, right: 1
        if s > 1e-6:
            return 1
        if s < -1e-6:
            return -1
        return 0

    def get_distance(self, lat, lng):
        nodes = self.nodes
        l = len(nodes)
        d = 0
        mdis = 1e99
        md = 0
        msgn = 0
        for i in range(1,l):
            p1 = latlng.Cartesian(0,0)
            p2 = latlng.LatLng(lat,lng).get_xy(latlng.LatLng(nodes[i-1].lat, nodes[i-1].lng))
            p3 = latlng.LatLng(lat,lng).get_xy(latlng.LatLng(nodes[i].lat, nodes[i].lng))
            sgn = self.leftright(p1, p2, p3)
            if (p3.x - p2.x)**2 + (p3.y - p2.y)**2 < 1e-1:
                continue
            k = ( (p1.x - p2.x)*(p3.x - p2.x) + (p1.y - p2.y)*(p3.y - p2.y) ) / ( (p3.x - p2.x)**2 + (p3.y - p2.y)**2 )
            foot = latlng.Cartesian(p2.x + k*(p3.x - p2.x), p2.y + k*(p3.y - p2.y))
            if p2.x <= foot.x and foot.x <= p3.x and p2.y <= foot.y and foot.y <= p3.y:
                d += math.sqrt( (p2.x-foot.x)**2 + (p2.y-foot.y)**2 )
                dis = math.sqrt( foot.x**2 + foot.y**2 )
                if dis < mdis:
                    mdis = dis
                    md = d
                    msgn = sgn
            else:
                d += math.sqrt( (p2.x-p3.x)**2 + (p2.y-p3.y)**2 )
        return (mdis, md, msgn)
        # mdis: distance betweeen (lat,lng) to foot
        # md:   distance from the beginning point (of the road) to foot
        # sgn:  (lat,lng) is on the left side (-1) or right side (1)

    def get_latlng(self, pos):
        if pos.index < len(self.nodes)-1:
            xy = self.nodes[pos.index].get_xy(self.nodes[pos.index+1])
            d = math.sqrt(xy.x ** 2 + xy.y ** 2)
            if d > 0:
                xy.x *= pos.dis/d
                xy.y *= pos.dis/d
            return(self.nodes[pos.index].get_latlng(xy.x, xy.y))
        else:
            return(self.nodes[pos.index])

    def plot_road(self, holdon = False, original = False, aggregated = True):
        ndx = []
        ndy = []
        for node in self.nodes:
            ndy.append(node.lat)
            ndx.append(node.lng)
        plt.plot(ndx, ndy, c = 'blue')
        # plt.plot(ndx, ndy)
        if original: self.aggregator.plot_original()
        if aggregated: self.aggregator.plot_aggregated()
        if holdon == False: plt.show()


class LocInRoad:

    def __init__(self, road, index, dis): # dis from node_index of road
        # if tdis < 0: out of range
        self.road = road
        self.index = index
        self.dis = dis
        if 0 <= index and index < len(road.distances):
            self.tdis = road.distances[index] + dis
            # total dis from beginning point
        else:
            self.tdis = -1

    def exist(self):
        if self.tdis < 0:
            return False
        return True

    def copy(self):
        return LocInRoad(self.road, self.index, self.dis)


class UoA:

    def __init__(self, road, pos_begin, pos_end):
        self.road = road
        self.pos_begin = pos_begin
        self.pos_end = pos_end
        self.length = self.pos_end.tdis - self.pos_begin.tdis
        self.workload = self.pos_end.tdis - self.pos_begin.tdis
        self.road.add_uoa(self)
        self.priority = pos_begin.index
        self.worked_min_dis = pos_begin.tdis
        self.worked_max_dis = pos_begin.tdis
        self.finished = False

    def plot(self, holdon = False):
        ndx = [self.road.get_latlng(self.pos_begin).lng,self.road.get_latlng(self.pos_end).lng]
        ndy = [self.road.get_latlng(self.pos_begin).lat,self.road.get_latlng(self.pos_end).lat]
        plt.plot(ndx, ndy, c = 'blue')
        if holdon == False: plt.show()

    def get_distance(self):
        return self.length

    def get_workload(self):
        return self.workload

    def update_range(self, pos):
        if self.pos_begin.tdis <= pos.tdis and pos.tdis <= self.pos_end.tdis:
            self.worked_min_dis = min(self.worked_min_dis, pos.tdis)
            self.worked_max_dis = max(self.worked_max_dis, pos.tdis)
            return True
        else:
            return False

    def get_density(self, tf, radius = 40):
        p = self.pos_begin.copy()
        rtrees = []
        while p.tdis <= self.pos_end.tdis:
            ll = self.road.get_latlng(p)
            trees = tf.find_trees(ll.lat,ll.lng,radius)
            for tree in trees:
                if tree not in rtrees:
                    d = self.road.get_distance(tree.lat, tree.lng)[1]
                    if self.pos_begin.tdis < d and d <= self.pos_end.tdis:
                        rtrees.append(tree)
            p = self.road.get_pos_from_to(p, 10)
            if p.exist() == False:
                break
        self.density = len(rtrees) / self.length
        return self.density
