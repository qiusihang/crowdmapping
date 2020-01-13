import numpy as np
import latlng
import treefinder
from matplotlib import pyplot as plt

class Aggregator:

    def __init__(self, density_calculation_radius = 2.5, tree_min_distance = 5):
        self.objects = []
        self.weights = []
        self.aggregated_objects = []
        self.threshold_1 = density_calculation_radius
        self.threshold_2 = tree_min_distance

    def add_object(self, lat, lng, weight = 1):
        self.objects.append(latlng.LatLng(lat, lng))
        self.weights.append(weight)

    def aggregate(self, worker_levels = 3):
    # threshold_1: radius for calculating density, threshold_2: min dis between trees
        num = len(self.objects)
        px = np.zeros(num)
        py = np.zeros(num)
        rho = np.zeros(num)
        alat = np.zeros(num)
        alng = np.zeros(num)
        if num < 1: return
        for i in range(1,num):
            xy = self.objects[0].get_xy(self.objects[i])
            px[i] = xy.x
            py[i] = xy.y
        for i in range(num):
            s = self.weights[i]
            #t = 1
            ave_x = px[i] * self.weights[i]
            ave_y = py[i] * self.weights[i]
            for j in range(num):
                if i!=j and (px[i]-px[j])**2 + (py[i]-py[j])**2 < self.threshold_1 **2:
                    #t += 1
                    s += self.weights[j]
                    ave_x += px[j] * self.weights[j]
                    ave_y += py[j] * self.weights[j]
            rho[i] = s + np.random.rand()*0.01
            ll = self.objects[0].get_latlng(ave_x/s, ave_y/s)
            alat[i] = ll.lat
            alng[i] = ll.lng

        dis = np.zeros(num)

        for i in range(num):
            m = 2147483647
            for j in range(num):
                if (rho[j] > rho[i]) and ((px[i]-px[j])**2 + (py[i]-py[j])**2 < m):
                    m = (px[i]-px[j])**2 + (py[i]-py[j])**2
            dis[i] = m

        self.aggregated_objects = []
        for i in range(num):
            if dis[i] > self.threshold_2**2 and rho[i] >= worker_levels:
                self.aggregated_objects.append(latlng.LatLng(alat[i],alng[i]))

    def aggregate_using_treefinder(self):
    # threshold_1: radius for calculating density, threshold_2: min dis between trees
    # only use this function when there are too many trees...
        num = len(self.objects)
        if num < 1: return
        objs = []
        for i in range(num):
            objs.append(treefinder.Tree(i, "", self.objects[i].lat, self.objects[i].lng))
        self.object_finder = treefinder.TreeFinder(None, objs)
        rho = np.zeros(num)
        alat = np.zeros(num)
        alng = np.zeros(num)
        for i in range(num):
            t = 0
            s = 0 #self.weights[i]
            ave_lat = 0 #self.objects[i].lat * self.weights[i]
            ave_lng = 0 #self.objects[i].lng * self.weights[i]
            nearby_objects = self.object_finder.find_trees(self.objects[i].lat, self.objects[i].lng, self.threshold_1)
            for tree in nearby_objects:
                t += 1
                s += self.weights[tree.id]
                ave_lat += tree.lat * self.weights[tree.id]
                ave_lng += tree.lng * self.weights[tree.id]
            rho[i] = t + np.random.rand()*0.99
            alat[i] = ave_lat/s
            alng[i] = ave_lng/s

        self.aggregated_objects = []
        for i in range(num):
            nearby_objects = self.object_finder.find_trees(self.objects[i].lat, self.objects[i].lng, self.threshold_2)
            flag = True
            for tree in nearby_objects:
                if rho[tree.id] > rho[i]:
                    flag = False
                    break
            if flag:
                self.aggregated_objects.append(latlng.LatLng(alat[i],alng[i]))


    def plot_original(self, holdon = False):
        num = len(self.objects)
        px = np.zeros(num)
        py = np.zeros(num)
        for i in range(num):
            px[i] = self.objects[i].lng
            py[i] = self.objects[i].lat
        plt.scatter(px,py,c='pink',marker='o',s=1)
        if holdon==False: plt.show()

    def plot_aggregated(self, holdon = False):
        num = len(self.aggregated_objects)
        px = np.zeros(num)
        py = np.zeros(num)
        for i in range(num):
            px[i] = self.aggregated_objects[i].lng
            py[i] = self.aggregated_objects[i].lat
        plt.scatter(px,py,c='red',marker='o',s=1)
        if holdon==False: plt.show()
