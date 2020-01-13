
import matplotlib.pyplot as plt
import numpy as np
import math
import latlng
import roadnetwork
import random
import treefinder
import worker
import taskassignment
import satellitemap
import os
import datetime
import shutil
import heapq
import settingparser

class Simulator:

    def __init__(self, filename = "simulation.setting"):
        self.agents = []
        self.simulation_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.setting = settingparser.SettingParser(filename)
        self.time = 0
        self.event_heap = EventHeap(key=lambda x:x.time)

        if not os.path.exists("output"):
            os.makedirs("output")
        if not os.path.exists("output/"+self.simulation_id):
            os.makedirs("output/"+self.simulation_id)
        shutil.copyfile(filename,"output/"+self.simulation_id+"/"+filename)

    def run(self, end_time = 3600):
        # add event create_agent
        self.event_heap.push(Event("create_agent",np.random.poisson(self.setting.worker_arrival_interval,1)[0]))
        # add events output
        k = 1
        while True:
            t = k * self.setting.time_stamp
            if t >= end_time: break
            self.event_heap.push(Event("output",t))
            k += 1
        # add event finish
        self.event_heap.push(Event("finish",end_time))

        while True:
            # get first event from heap
            event = self.event_heap.pop()
            self.time = event.time

            if event.type == "create_agent":
                agent = self.create_agent()
                if len(agent.worker.task.uoas) > 0: # task has uoa.. meaning still has task to do
                    self.agents.append(agent)
                    uoa_finish_time = agent.execute()
                    self.event_heap.push(Event("agent_finish_uoa",self.time + uoa_finish_time, agent))
                    self.event_heap.push(Event("agent_dropout",self.time + self.setting.dropout_time, agent))
                    self.event_heap.push(Event("create_agent",self.time + np.random.poisson(self.setting.worker_arrival_interval,1)[0]))

            if event.type == "agent_finish_uoa":
                if event.agent.finish_uoa():
                    uoa_finish_time = event.agent.execute()
                    self.event_heap.push(Event("agent_finish_uoa",self.time + uoa_finish_time, event.agent))
                else:
                    if event.agent in self.agents:
                        self.agents.remove(event.agent)

            if event.type == "agent_dropout":
                if event.agent in self.agents:
                    self.agents.remove(event.agent)

            if event.type == "output":
                self.output()

            if event.type == "finish":
                self.output()
                return

    def worker_parameter(self, i, pname):
        if pname == "recall":
            r = random.normalvariate(self.setting.worker_labeling_recall[i],self.setting.worker_labeling_recall_std[i])
            if r > 1.0: r = 1
            if r < 0.1: r = 0.1
            return r
        if pname == "precision":
            p = random.normalvariate(self.setting.worker_labeling_precision[i],self.setting.worker_labeling_precision_std[i])
            if p > 1.0: p = 1
            if p < 0.1: p = 0.1
            return p
        if pname == "error":
            e = random.normalvariate(self.setting.worker_labeling_error[i],self.setting.worker_labeling_error_std[i])
            if e > 4.5: e = 4.5
            if e < 0.5: e = 0.5
            return e

    def create_agent(self):
        p = random.random()
        probability = 0
        for i in range(len(self.setting.worker_level_distribution)):
            probability += self.setting.worker_level_distribution[i]
            if i == len(self.setting.worker_level_distribution) - 1:
                probability = 1
            if p <= probability:
                agent = Agent(\
                self.setting.wm, i, self.time, self.setting.tf,\
                self.worker_parameter(i,"recall"),\
                self.worker_parameter(i,"precision"),\
                self.setting.worker_labeling_error[i],\
                self.setting.worker_labeling_error_std[i],\
                self.setting.worker_exploring_time[i],\
                self.setting.worker_labeling_time[i])
                break
        return agent

    def output(self):
        for property in self.setting.output_properties:
            foldername = "output/"+self.simulation_id+"/"+property
            if property == "tree_cover":
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                if self.setting.prediction_with_satellite_map:
                    sm = self.setting.sm
                else:
                    sm = None
                self.setting.tf.calc_performance(self.setting.rn, foldername+"/"+str(self.time)+".txt", sm)
            if property == "density":
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                self.setting.tf.calc_density_performance(self.setting.rn, foldername+"/"+str(self.time)+".txt")
            elif property == "cost":
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                f = open(foldername+"/"+str(self.time)+".txt","w")
                s = sum([worker.workload for worker in self.setting.wm.workers])
                f.write("cost = " + str(s*self.setting.payment_per_workload) + "\n")
                f.close()
            elif property == "worker_statistics":
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                self.setting.wm.output_stat(foldername+"/"+str(self.time)+".txt")
            elif property == "task_statistics":
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                self.setting.ta.output_stat(foldername+"/"+str(self.time)+".txt")
            #elif property == "UOA_statistic":
            #    if not os.path.exists(foldername):
            #        os.makedirs(foldername)
            elif property == "image":
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                self.plot(foldername+"/"+str(self.time)+".png")

    def plot(self, filename = ''):
        self.setting.rn.plot_map(True)
        self.setting.rn.aggregator.plot_aggregated(True)
        for road in self.setting.rn.roads:
            road.predictor.plot(True)
        if len(filename) > 0:
            plt.savefig(filename)
        else:
            plt.show()


class Event:

    def __init__(self, type, time, agent = None):
        self.type = type
        self.time = time
        self.agent = agent

class EventHeap:

    def __init__(self, key=lambda x:x):
        self.key = key
        self._data = []
        self.count = 0

    def push(self, item):
        self.count += 1
        heapq.heappush(self._data, [self.key(item), self.count, item])

    def pop(self):
        return heapq.heappop(self._data)[2]

    def heapify(self):
        heapq.heapify(self._data)


class Agent:

    def __init__(self, wm, level, time, tf, lr, lp, le, les, et, lt):
    #treefinder, probability of label or not, standard deviation of labeling error, labeling time,
    #moving distance, moving time
        self.tree_finder            = tf
        self.labeling_recall        = lr
        self.labeling_precision     = lp
        self.labeling_error         = le
        self.labeling_error_std     = les
        self.exploring_time         = et
        self.labeling_time          = lt
        self.worker                 = wm.new_worker(1-le/5+lr+lp,level,time)

    def execute(self):
        uoa = self.worker.task.uoas[self.worker.uoa_id]
        trees = []
        execution_time = 0
        if_break = False
        for i in range(100):
            ll = uoa.road.get_latlng(self.worker.cur_pos)
            nearby_trees = self.tree_finder.find_trees(ll.lat, ll.lng, 40)
            for tree in nearby_trees:
                if tree not in trees:
                    trees.append(tree)
            if if_break: break
            if self.worker.move(10) == False:
                if self.worker.set_position(uoa.length-1) == False:
                    break
                if_break = True
        for tree in trees:
            if random.random() < self.labeling_recall:
                while True:
                    p = random.random()
                    r = random.normalvariate(self.labeling_error, self.labeling_error_std)
                    if p < self.labeling_precision:
                        while abs(r) >= 5:
                            r = random.normalvariate(self.labeling_error, self.labeling_error_std)
                    else:
                        while abs(r) <= 5:
                            r = random.normalvariate(10, 5)
                    theta = random.random() * math.pi
                    ll_tree = latlng.LatLng(tree.lat, tree.lng).get_latlng(r*math.cos(theta),r*math.sin(theta))
                    self.worker.label(ll_tree.lat, ll_tree.lng)
                    execution_time += self.labeling_time
                    if p < self.labeling_precision: break
        execution_time += self.worker.task.uoas[self.worker.uoa_id].length * self.exploring_time
        return execution_time

    def finish_uoa(self):
        self.worker.submit(self.worker.uoa_id)
        if self.worker.uoa_id + 1 >= len(self.worker.task.uoas):
            return False
        self.worker.shift_uoa()
        return True
