import matplotlib.pyplot as plt
import latlng
import math
import geopredictor

class Tree:
    def __init__(self, id, category, lat, lng):
        self.category = category
        self.lat = lat
        self.lng = lng
        self.id = id

class TreeFinder:

    def __init__(self, filename, initial_trees = [], grid_size = 5):
        self.tree_finder = []
        self.trees = initial_trees
        self.count = 0
        self.max_lat = -1e99
        self.min_lat = 1e99
        self.max_lng = -1e99
        self.min_lng = 1e99
        self.grid_size = grid_size
        tid = len(self.trees)
        if filename is not None and filename != "":
            for line in open(filename,'r'):
                temp = line.split(';')
                tree = Tree(tid, temp[0],float(temp[1]),float(temp[2]))
                tid += 1
                self.trees.append(tree)
        for tree in self.trees:
            self.max_lat = max(self.max_lat, tree.lat)
            self.min_lat = min(self.min_lat, tree.lat)
            self.max_lng = max(self.max_lng, tree.lng)
            self.min_lng = min(self.min_lng, tree.lng)
        w = latlng.LatLng(self.min_lat, self.min_lng).get_xy(latlng.LatLng(self.min_lat, self.max_lng)).x
        h = latlng.LatLng(self.min_lat, self.min_lng).get_xy(latlng.LatLng(self.max_lat, self.min_lng)).y
        self.n_lat = int(h / grid_size) + 1
        self.n_lng = int(w / grid_size) + 1
        self.k_lat = int((self.n_lat-1)/(self.max_lat-self.min_lat))
        self.k_lng = int((self.n_lng-1)/(self.max_lng-self.min_lng))
        for i in range(self.n_lat):
            self.tree_finder.append([])
            for j in range(self.n_lng):
                self.tree_finder[i].append([])
        self.tree_vis = [False for tree in self.trees]
        for tree in self.trees:
            self.add_tree(tree)

    def add_tree(self, tree):
        i = int((tree.lat - self.min_lat) * self.k_lat)
        j = int((tree.lng - self.min_lng) * self.k_lng)
        self.tree_finder[i][j].append(tree)
        self.count += 1

    def find_trees(self, lat, lng, radius = 5):
        trees = []
        grid_range = int((radius-0.1)/self.grid_size) + 1
        i = int((lat - self.min_lat) * self.k_lat)
        j = int((lng - self.min_lng) * self.k_lng)
        for p in range(i-grid_range,i+grid_range+1):
            for q in range(j-grid_range,j+grid_range+1):
                if 0 <= p and p < self.n_lat and 0<=q and q < self.n_lng:
                    for tree in self.tree_finder[p][q]:
                        if latlng.LatLng(lat,lng).get_distance(latlng.LatLng(tree.lat,tree.lng)) < radius:
                            trees.append(tree)
        return trees

    def find_the_nearest_tree(self, lat, lng, radius = 5):
        grid_range = int((radius-0.1)/self.grid_size) + 1
        i = int((lat - self.min_lat) * self.k_lat)
        j = int((lng - self.min_lng) * self.k_lng)
        m_dis = 1e99
        m_tree = None
        for p in range(i-grid_range,i+grid_range+1):
            for q in range(j-grid_range,j+grid_range+1):
                if 0 <= p and p < self.n_lat and 0<=q and q < self.n_lng:
                    for tree in self.tree_finder[p][q]:
                        if self.tree_vis[tree.id] == False:
                            dis = latlng.LatLng(lat,lng).get_distance(latlng.LatLng(tree.lat,tree.lng))
                            if dis < m_dis and dis < radius:
                                m_dis = dis
                                m_tree = tree
        return m_tree

    def calc_performance(self, roadnetwork, filename = "", satmap = None):
        TP_a = 0
        TN_a = 0
        recall_a = 0
        precision_a = 0
        rmse_a = 0

        TP_p = 0
        TN_p = 0
        recall_p = 0
        precision_p = 0
        rmse_p = 0

        self.tree_vis = [False for tree in self.trees]
        roadnetwork.aggregate()
        for aggregated_tree in roadnetwork.aggregator.aggregated_objects:
            nt = self.find_the_nearest_tree(aggregated_tree.lat, aggregated_tree.lng, 5)
            if nt is None:
                TN_a += 1
                continue
            TP_a += 1
            self.tree_vis[nt.id] = True
            rmse_a += aggregated_tree.get_distance(latlng.LatLng(nt.lat, nt.lng)) ** 2

        if TP_a > 0:
            precision_a = TP_a/(TP_a+TN_a)
            recall_a = TP_a/self.count
            rmse_a = math.sqrt(rmse_a / TP_a)

        # self.tree_vis = [False for tree in self.trees]
        for road in roadnetwork.roads:
            p = geopredictor.Predictor(road)
            p.predict()
            if satmap is not None:
                p.combine_satmap(satmap)
            for tree in p.predicted_objects:
                nt = self.find_the_nearest_tree(tree.lat, tree.lng, 5)
                if nt is None:
                    TN_p += 1
                    continue
                TP_p += 1
                self.tree_vis[nt.id] = True
                rmse_p += tree.get_distance(latlng.LatLng(nt.lat, nt.lng)) ** 2

        if TP_p > 0:
            precision_p = TP_p/(TP_p+TN_p)
            recall_p = TP_p/self.count
            rmse_p = math.sqrt(rmse_p / TP_p)

        if filename != "":
            f = open(filename,"w")
            f.write("recall = " + str(recall_a) + "\n")
            f.write("precision = " + str(precision_a) + "\n")
            f.write("RMSE of labeling error = " + str(rmse_a) + "\n")
            f.write("precall = " + str(recall_p) + "\n")
            f.write("pprecision = " + str(precision_p) + "\n")
            f.write("pRMSE of labeling error = " + str(rmse_p) + "\n")
            f.close()

        return recall_a, precision_a, rmse_a

    def calc_density_performance(self, rn, filename):
        MSE = 0
        AVE = 0
        MSE_p = 0
        AVE_p = 0
        t = 0
        t_p = 0
        n = 0
        n_p = 0
        n2 = 0
        n2_p = 0
        for road in rn.roads:
            for i in range(len(road.uoas)):
                t_p += 1
                if road.uoas[i].finished:
                    t += 1
                    MSE += ( road.predictor.mc[i]/road.uoas[i].length - road.uoas[i].density ) ** 2
                    AVE += road.predictor.mc[i]/road.uoas[i].length - road.uoas[i].density
                    if abs( int(road.predictor.mc[i] - road.uoas[i].density*road.uoas[i].length )) == 0:
                        n+=1
                        n2+=1
                    elif abs( road.predictor.mc[i]/road.uoas[i].length - road.uoas[i].density ) <= road.uoas[i].density * 0.2:
                        n2+=1
                else:
                    MSE_p += ( road.predictor.predicted_mc[i]/road.uoas[i].length - road.uoas[i].density ) ** 2
                    AVE_p += road.predictor.predicted_mc[i]/road.uoas[i].length - road.uoas[i].density
                    if abs( int(road.predictor.predicted_mc[i] - road.uoas[i].density*road.uoas[i].length )) == 0:
                        n_p+=1
                        n2_p+=1
                    elif abs( road.predictor.predicted_mc[i]/road.uoas[i].length - road.uoas[i].density ) <= road.uoas[i].density * 0.2:
                        n2_p+=1
        if t > 0:
            MSE /= t
            AVE /= t
        if t_p - t > 0:
            MSE_p /= (t_p - t)
            AVE_p /= (t_p - t)
        else:
            MSE_p = 0
        f = open(filename,"w")
        f.write("Progress = " + str(t/t_p) + "\n")
        f.write("MSE = " + str(MSE) + "\n")
        f.write("MSE prediction = " + str(MSE_p) + "\n")
        f.write("MAE = " + str(AVE) + "\n")
        f.write("MAE prediction = " + str(AVE_p) + "\n")
        f.write("Recall = " + str(n / t_p) + "\n")
        f.write("Recall prediction = " + str((n+n_p) / t_p) + "\n")
        f.write("Relaxed Recall = " + str(n2 / t_p) + "\n")
        f.write("Relaxed Recall prediction = " + str((n2+n2_p) / t_p) + "\n")
        f.close()

    def plot(self, holdon = False):
        px = []
        py = []
        for tree in self.trees:
            px.append(tree.lng)
            py.append(tree.lat)
        plt.scatter(px,py,c=[0.3,0.8,0.3],marker='o',s=1)
        if holdon==False: plt.show()
