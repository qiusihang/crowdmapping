import bisect
import roadnetwork
import satellitemap
import predictor
import taskassignment

class Worker:

    def __init__(self, wm, level, start_time):
        self.id = wm.count
        self.strat_time = start_time
        self.status = 0 # 0:working, 1:exit
        self.wm = wm
        self.level = level
        self.labels = 0
        self.wm.ta.assign_task(self)
        self.uoa_id = 0
        if len(self.task.uoas) > 0:
            self.cur_pos = self.task.uoas[self.uoa_id].pos_begin.copy()
        self.uoa_move_distances = [0 for uoa in self.task.uoas]
        self.workload = 0

    def shift_uoa(self, uoa_id = -1):
        if uoa_id == -1:
            self.uoa_id += 1
        else:
            self.uoa_id = uoa_id
        self.uoa_id %= len(self.task.uoas)
        self.cur_pos = self.task.uoas[self.uoa_id].pos_begin.copy()
        return True

    def set_position(self, distance): # distance from starting point
        if self.uoa_id >= len(self.task.uoas):
            return False
        uoa = self.task.uoas[self.uoa_id]
        next_pos = uoa.road.get_pos_from_to(self.task.uoas[self.uoa_id].pos_begin, distance)
        if uoa.update_range(next_pos) == False:
            return False
        self.uoa_move_distances[self.uoa_id] = max(self.uoa_move_distances[self.uoa_id], next_pos.tdis - uoa.pos_begin.tdis)
        self.cur_pos = next_pos
        return True

    def move(self, distance = 5):
        if self.uoa_id >= len(self.task.uoas):
            return False
        uoa = self.task.uoas[self.uoa_id]
        next_pos = uoa.road.get_pos_from_to(self.cur_pos, distance)
        if uoa.update_range(next_pos) == False:
            return False
        self.uoa_move_distances[self.uoa_id] = max(self.uoa_move_distances[self.uoa_id], next_pos.tdis - uoa.pos_begin.tdis)
        self.cur_pos = next_pos
        self.workload += distance
        return True

    def label(self, lat, lng):
        if self.uoa_id >= len(self.task.uoas):
            return
        uoa = self.task.uoas[self.uoa_id]
        if self.wm.ta.strategy > 1:
            uoa.road.aggregator.add_object(lat, lng, self.level + 1)
        else:
            uoa.road.aggregator.add_object(lat, lng)
        self.labels += 1
        self.workload += 2.5

    def task_validation(self):
        s1 = 0
        s2 = 0
        for i in range(len(self.task.uoas)):
            s1 += self.uoa_move_distances[i]
            s2 += self.task.uoas[i].length
        return s1/s2

    def submit(self, i):
        uoa = self.task.uoas[i]
        self.task.submision_times[i] += 1
        if self.task.submision_times[i] >= len(self.task.workers):
            uoa.finished = True
            road = uoa.road
            road.aggregator.aggregate(self.wm.ta.strategy)
            if self.wm.feedback_with_prediction:
                road.predictor.predict()
            else:
                road.predictor.predict(False)
            self.wm.ta.uoa_heap.heapify()
            #if self.wm.prediction_with_satellite_map:
            #    road.predictor.combine_satmap(self.wm.sm)

class WorkerManager:

    def __init__(self, rn, ta, sm):
    #roadnetwork, taskassignment, satellitemap
        self.workers = []
        self.qualities = []
        self.count = 0
        self.rn = rn
        self.ta = ta
        self.sm = sm
        self.prediction_with_satellite_map = False
        self.feedback_with_prediction = True

    def new_worker(self, q, level, start_time):
        #0:low-skill, 1:medium-skill, 2:high-skill
        if self.count < 100:
            worker = Worker(self, level, start_time)
            bisect.insort(self.qualities, q)
        else:
            pos = bisect.bisect(self.qualities, q)
            if pos / self.count < 1/3:
                l = 0
            elif pos / self.count < 2/3:
                l = 1
            else:
                l = 2
            worker = Worker(self, l, start_time)
            bisect.insort(self.qualities, q)
        self.workers.append(worker)
        self.count += 1
        return worker

    def output_stat(self, filename):
        f = open(filename,"w")
        f.write(str(len(self.workers))+"\n")
        for worker in self.workers:
            f.write("\nID = "+str(worker.id) + "\n")
            f.write("level = "+str(worker.level) + "\n")
            f.write("workeload = "+str(worker.workload) + "\n")
            f.write("complete = "+str(worker.task_validation()) + "\n")
            f.write("labels = "+str(worker.labels) + "\n")
            f.write("status = "+str(worker.status) + "\n")
        f.close()
