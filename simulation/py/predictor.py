import math
import numpy as np
import latlng
import satellitemap
import random
from matplotlib import pyplot as plt

class Predictor:

    def __init__(self, road, state_set = range(30)):
        self.road = road
        self.state_set = state_set
        self.dp = None
        self.update()

    def update(self):
        self.mc = [-1 for uoa in self.road.uoas]
        self.predicted_mc = [-1 for uoa in self.road.uoas]
        for i in range(len(self.road.uoas)):
            if self.road.uoas[i].finished:
                self.mc[i] = 0
        object_pos = []
        for object in self.road.aggregator.aggregated_objects:
            object_pos.append(self.road.get_distance(object.lat, object.lng)[1])
        for dis in object_pos:
            for i in range(len(self.road.uoas)):
                if self.mc[i] < 0 : continue
                uoa = self.road.uoas[i]
                if uoa.pos_begin.tdis < dis and dis <= uoa.pos_end.tdis:
                    self.mc[i] += 1
                    break

    def get_probability(self,x,y): #p(x|y)
        if y < 0:
            return 0
        x = x + 2
        mean = y + 1
        variance = 0.08
        mu = math.log(mean/math.sqrt(1+variance/mean/mean))
        sigma = math.sqrt(math.log(1+variance/mean/mean))
        return 1/(x * sigma * math.sqrt(2*math.pi)) * math.exp( - (math.log(x) - mu)**2/(2*sigma*sigma) )

    def predict(self, feedback_with_prediction = True):

        # Tips:
        # For high-density urban objects that distributed relatively evenly,
        # like trees or lamp posts, simply predicting un-mapped road segment
        # using average density can acquire compararble results compared to
        # dynamic programming and max-likelihood.

        self.update()
        if len(self.mc) < 3:
            if self.mc[0] == -1:
                return
            if self.mc[-1] == -1:
                self.predicted_mc[-1] = self.mc[0]
        else:
            if self.mc[0] == -1 or self.mc[-1] == -1:
                return
            self.dp = [{} for i in self.mc]
            self.pre = [{} for i in self.mc]
            for i in range(len(self.mc)):
                self.dp[i][self.mc[i]] = 0
                if i > 0:
                    for s2 in self.state_set:
                        self.dp[i][s2] = 0
                        for s in self.dp[i-1]:
                            p = self.get_probability(s2,s) # p(s2|s)
                            if self.dp[i-1][s] * p > self.dp[i][s2]:
                                self.dp[i][s2] = self.dp[i-1][s] * p
                                self.pre[i][s2] = s
                if self.mc[i] >= 0:
                    self.dp[i] = {self.mc[i]: 1}
            for i in range(len(self.mc)):
                j = len(self.mc) - i - 1
                self.predicted_mc[j] = self.mc[j]
                if self.dp[j][self.mc[j]] < 1 and self.predicted_mc[j+1] in self.pre[j+1].keys():
                    self.predicted_mc[j] = self.pre[j+1][self.predicted_mc[j+1]]
                    self.road.uoas[j].workload = self.road.uoas[j].length + 2.5 * self.predicted_mc[j]
        if feedback_with_prediction:
            self.update_priority()  # Max Likelihood
        else:
            self.update_priority2() # Random

    def update_priority(self):
        if len(self.mc) < 1:
            self.update()
        self.priority = [1 for i in self.mc]
        self.priority[0] = -1 + 1 / len(self.mc)
        if len(self.mc) < 3:
            self.priority[0] = 1
            self.priority[len(self.mc)-1] = 1
        else:
            self.priority[len(self.mc)-1] = -1 + 1 / len(self.mc)
        if len(self.mc) > 2:
            self.priority[int((len(self.mc)-1)/2)] = 1 + 1 / len(self.mc)
            o = 2
            for i in range(len(self.mc)):
                if self.priority[i] == 0:
                    self.priority[i] = 1 + o / len(self.mc)
                    o += 1
            for i in range(1, len(self.mc)):
                if self.mc[i] >= 0 and self.mc[i-1] < 0:
                    p = self.dp[i-1][self.predicted_mc[i-1]] * self.get_probability(self.predicted_mc[i-1], self.mc[i])
                    k = i-1
                    while k >= 0:
                        if self.mc[k-1] < 0:
                            self.priority[k] = self.get_probability(self.predicted_mc[k-1], self.predicted_mc[k-1])
                        else:
                            self.priority[k] = self.get_probability(self.mc[k-1], self.predicted_mc[k-1])
                        k -= 1
                        if self.mc[k] >= 0:
                            break
        for i in range(len(self.mc)):
            k = int((self.road.uoas[i].priority+10)/100)
            self.road.uoas[i].priority = self.priority[i] + k * 100

    def update_priority2(self):
        if len(self.mc) < 1:
            self.update()
        self.priority = [random.random() for i in self.mc]
        for i in range(len(self.mc)):
            k = int((self.road.uoas[i].priority+10)/100)
            self.road.uoas[i].priority = self.priority[i] + k * 100

    def entropy(self,p):
        return -p*math.log(p)

    def plot(self, holdon = False):
        px = []
        py = []
        for i in range(len(self.mc)):
            if self.mc[i] < 0 and self.predicted_mc[i] > 0:
                uoa = self.road.uoas[i]
                pos = uoa.pos_begin.copy()
                dis = uoa.get_distance() / self.predicted_mc[i]
                for j in range(self.predicted_mc[i]):
                    ll = uoa.road.get_latlng(pos)
                    px.append(ll.lng)
                    py.append(ll.lat)
                    pos = uoa.road.get_pos_from_to(pos, dis)
                    if pos.tdis < 0: break
        plt.scatter(px,py,c=[0.5,0.8,0.5],marker='o',s=1)
        if holdon==False: plt.show()
