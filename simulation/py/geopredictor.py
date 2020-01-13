import math
import numpy as np
import latlng
import roadnetwork
import satellitemap
from matplotlib import pyplot as plt

class Predictor:

    def __init__(self, road):
        # cur_pos: (lat, lng)
        self.road = road
        self.predicted_objects = []

    def calc_ave(self, dis_begin, dis_end):
        if dis_end <= dis_begin:
            #return (5, 20, dis_begin, 5, 20, dis_begin)
            return (0, 0, 0, 0, 0, 0)
        ave_left_d1 = ave_left_d2_diff = 0
        ave_right_d1 = ave_right_d2_diff = 0
        left_d2 = []
        right_d2 = []
        for node in self.road.aggregator.aggregated_objects:
            (d1, d2, sgn) = self.road.get_distance(node.lat, node.lng)
            if d1 > 1e10 or d2 > 1e10: continue
            if sgn < 0:
                ave_left_d1 += d1
                left_d2.append(d2)
            if sgn > 0:
                ave_right_d1 += d1
                right_d2.append(d2)
        ll = len(left_d2)
        lr = len(right_d2)
        if ll > 0: ave_left_d1  /= ll
        if lr > 0: ave_right_d1 /= lr
        left_d2.sort()
        ll2 = max_left_d2 = 0
        for i in range(1,ll):
            if dis_begin <= left_d2[i-1] and left_d2[i] <= dis_end:
                ave_left_d2_diff += left_d2[i] - left_d2[i-1]
                max_left_d2 = max(max_left_d2, left_d2[i])
                ll2 += 1
        right_d2.sort()
        lr2 = max_right_d2 = 0
        for i in range(1,lr):
            if dis_begin <= right_d2[i-1] and right_d2[i] <= dis_end:
                ave_right_d2_diff += right_d2[i] - right_d2[i-1]
                max_right_d2 = max(max_right_d2, right_d2[i])
                lr2 += 1
        if ll2 > 1: ave_left_d2_diff  /= ll2
        if lr2 > 1: ave_right_d2_diff /= lr2
        return (ave_left_d1, ave_left_d2_diff, max_left_d2, ave_right_d1, ave_right_d2_diff, max_right_d2)


    def predict_segment(self, dis_begin, dis_end, ave_values):
        (ave_left_d1, ave_left_d2_diff, max_left_d2, ave_right_d1, ave_right_d2_diff, max_right_d2) = ave_values

        pos = self.road.get_pos_of(max_left_d2)
        while ave_left_d2_diff > 0:
            pos = self.road.get_pos_from_to(pos, ave_left_d2_diff)
            if pos.tdis < 0 or pos.tdis >= dis_end: break
            if pos.tdis < dis_begin:                continue
            if pos.index >= len(self.road.nodes):   break
            v1 = self.road.nodes[pos.index].get_xy(self.road.nodes[pos.index+1])
            d1 = math.sqrt(v1.x**2 + v1.y**2)
            if d1 > 0:
                v1.x = v1.x / d1 * pos.dis
                v1.y = v1.y / d1 * pos.dis
                v2 = latlng.Cartesian(-v1.y,v1.x)
                d2 = math.sqrt(v2.x**2 + v2.y**2)
                v2.x = v2.x / d2 * ave_left_d1
                v2.y = v2.y / d2 * ave_left_d1
                self.predicted_objects.append( self.road.nodes[pos.index].get_latlng(v1.x+v2.x, v1.y+v2.y) )

        pos = self.road.get_pos_of(max_right_d2)
        while ave_right_d2_diff > 0:
            pos = self.road.get_pos_from_to(pos, ave_right_d2_diff)
            if pos.tdis < 0 or pos.tdis >= dis_end: break
            if pos.tdis < dis_begin:                continue
            if pos.index >= len(self.road.nodes):   break
            v1 = self.road.nodes[pos.index].get_xy(self.road.nodes[pos.index+1])
            d1 = math.sqrt(v1.x**2 + v1.y**2)
            if d1 > 0:
                v1.x = v1.x / d1 * pos.dis
                v1.y = v1.y / d1 * pos.dis
                v2 = latlng.Cartesian(v1.y,-v1.x)
                d2 = math.sqrt(v2.x**2 + v2.y**2)
                v2.x = v2.x / d2 * ave_right_d1
                v2.y = v2.y / d2 * ave_right_d1
                self.predicted_objects.append( self.road.nodes[pos.index].get_latlng(v1.x+v2.x, v1.y+v2.y) )

    def predict(self):
        if len(self.road.uoas) == 0:
            #self.predict_segment(0, self.road.distances[-1],self.calc_ave(0, self.road.distances[-1]))
            return
        self.predicted_objects = []
        self.road.uoas.sort(key = lambda x:x.worked_min_dis)
        current_min_dis = self.road.uoas[0].worked_min_dis
        current_max_dis = self.road.uoas[0].worked_max_dis
        for uoa in self.road.uoas:
            if uoa.worked_max_dis <= uoa.worked_min_dis: continue
            if uoa.worked_min_dis > current_max_dis:
                self.predict_segment(current_max_dis, uoa.worked_min_dis, self.calc_ave(current_min_dis,current_max_dis))
                current_min_dis = uoa.worked_min_dis
            current_max_dis = max(current_max_dis, uoa.worked_max_dis)
        self.predict_segment(current_max_dis, self.road.distances[-1], self.calc_ave(current_min_dis,current_max_dis))

    def combine_satmap(self, satmap):
        for node in self.predicted_objects:
            if satmap.is_tree(node.lat, node.lng) == False:
                self.predicted_objects.remove(node)

    def plot(self, holdon = False):
        num = len(self.predicted_objects)
        px = np.zeros(num)
        py = np.zeros(num)
        for i in range(num):
            px[i] = self.predicted_objects[i].lng
            py[i] = self.predicted_objects[i].lat
        plt.scatter(px,py, c='green', marker='+')
        if holdon==False: plt.show()
