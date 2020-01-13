import roadnetwork
import treefinder
import worker
import taskassignment
import satellitemap

class SettingParser:

    def __init__(self, filename):
        self.rn = None
        self.tf = None
        self.sm = None
        self.ta = None

        self.expected_workload = 500
        self.payment_per_workload = 0.01
        self.dropout_time = 1000

        self.worker_arrival_interval = 30
        self.worker_level_distribution = [0.333, 0.333, 0.333]
        self.worker_exploring_time = [3, 3, 3]
        self.worker_labeling_time = [8, 8, 8]
        self.worker_labeling_recall = [0.5, 0.7, 0.9]
        self.worker_labeling_precision = [0.5, 0.7, 0.9]
        self.worker_labeling_error = [4, 3, 2]
        self.worker_labeling_recall_std = [0, 0, 0]
        self.worker_labeling_precision_std = [0, 0, 0]
        self.worker_labeling_error_std = [0, 0, 0]

        self.strategy = 0
        self.feedback_with_prediction = True
        self.prediction_with_satellite_map = True

        self.time_stamp = 100
        self.output_properties = []

        for line in open(filename):
            line = line.replace(' ','')
            line = line.replace('\n','')
            line = line.replace('\r','')
            if len(line) < 1:
                continue
            if line[0] != '#':
                args = line.split('=')
                if args[0] == "road_network":
                    self.rn = roadnetwork.RoadNetwork(args[1])
                elif args[0] == "ground_truth":
                    self.tf = treefinder.TreeFinder(args[1])
                elif args[0] == "satellite_map":
                    params = args[1].split(',')
                    foldername = None
                    if len(params) > 4:
                        foldername = params[5]
                        params.remove(foldername)
                    params = [float(x) for x in params]
                    if len(params) > 4:
                        self.sm = satellitemap.SatelliteMap(params[0], params[1], params[2], params[3], params[4], foldername)

                elif args[0] == "expected_workload":
                    self.expected_workload = int(args[1])
                elif args[0] == "payment_per_workload":
                    self.payment_per_workload = float(args[1])
                elif args[0] == "dropout_time":
                    self.dropout_time = int(args[1])

                elif args[0] == "worker_arrival_interval":
                    params = args[1].split(',')
                    self.worker_arrival_interval = int(params[0])
                elif args[0] == "worker_level_distribution":
                    params = args[1].split(',')
                    self.worker_level_distribution = [float(x) for x in params]
                elif args[0] == "worker_exploring_time":
                    params = args[1].split(',')
                    self.worker_exploring_time = [float(x) for x in params]
                elif args[0] == "worker_labeling_time":
                    params = args[1].split(',')
                    self.worker_labeling_time = [float(x) for x in params]
                elif args[0] == "worker_labeling_recall":
                    params = args[1].split(',')
                    self.worker_labeling_recall = [float(x) for x in params]
                elif args[0] == "worker_labeling_precision":
                    params = args[1].split(',')
                    self.worker_labeling_precision = [float(x) for x in params]
                elif args[0] == "worker_labeling_error":
                    params = args[1].split(',')
                    self.worker_labeling_error = [float(x) for x in params]
                elif args[0] == "worker_labeling_recall_std":
                    params = args[1].split(',')
                    self.worker_labeling_recall_std = [float(x) for x in params]
                elif args[0] == "worker_labeling_precision_std":
                    params = args[1].split(',')
                    self.worker_labeling_precision_std = [float(x) for x in params]
                elif args[0] == "worker_labeling_error_std":
                    params = args[1].split(',')
                    self.worker_labeling_error_std = [float(x) for x in params]

                elif args[0] == "task_assignment_strategy":
                    if args[1] == "single_queue":
                        self.strategy = 0
                    elif args[1] == "multi_queue":
                        self.strategy = 3
                elif args[0] == "feedback_with_prediction":
                    if args[1] == "true" or args[1] == "True" or args[1] == "TRUE":
                        self.feedback_with_prediction = True
                    else:
                        self.feedback_with_prediction = False
                elif args[0] == "prediction_with_satellite_map":
                    if args[1] == "true" or args[1] == "True" or args[1] == "TRUE":
                        self.prediction_with_satellite_map = True
                    else:
                        self.prediction_with_satellite_map = False

                elif args[0] == "time_stamp":
                    self.time_stamp = int(args[1])
                elif args[0] == "output_properties":
                    self.output_properties = args[1].split(',')

        if self.rn == None or self.tf == None:
            return

        for road in self.rn.roads:
            for uoa in road.uoas:
                uoa.get_density(self.tf)

        self.ta = taskassignment.TaskAssignment(self.rn, self.strategy, self.expected_workload, self.feedback_with_prediction)
        self.wm = worker.WorkerManager(self.rn, self.ta, self.sm)
        self.wm.prediction_with_satellite_map = self.prediction_with_satellite_map
        self.wm.feedback_with_prediction = self.feedback_with_prediction
