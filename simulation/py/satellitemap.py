import latlng
import math
import os
import requests
import PIL.Image as Image
import numpy as np
import matplotlib.pyplot as plt

class SatelliteMap:

    def __init__(self, lat_N, lat_S, lng_W, lng_E, zoom = 17, foldername = None, size = 400):
        if lat_S > lat_N or lng_W > lng_E:
            return
        self.lat_N = lat_N
        self.lat_S = lat_S
        self.lng_W = lng_W
        self.lng_E = lng_E
        self.zoom = zoom
        self.size = size
        self.meters_per_pixel = 156543.03392 * math.cos(52 * math.pi / 180) / (2.0 ** zoom)
        if foldername is not None:
            self.folder_name = "input/"+foldername
        else:
            self.folder_name = "input/"+str(lat_N*lat_S*lng_W*lng_E*zoom)

        folder = os.path.exists(self.folder_name)
        if not folder:
            os.makedirs(self.folder_name)
        folder = os.path.exists(self.folder_name + "/vi")
        if not folder:
            os.makedirs(self.folder_name+"/vi")

        self.grid = [[]]
        ll = latlng.LatLng(lat_N, lng_W)
        while True:
            self.grid[0].append(ll)
            ll = ll.get_latlng(self.meters_per_pixel * size, 0)
            if ll.lng > lng_E:
                break

        ll = latlng.LatLng(lat_N, lng_W)
        while True:
            ll = ll.get_latlng(0, - self.meters_per_pixel * size)
            if ll.lat < lat_S:
                break
            self.grid.append([ll])

        for i in range(1,len(self.grid)):
            for j in range(1,len(self.grid[0])):
                self.grid[i].append( self.grid[i-1][j].get_latlng(0, - self.meters_per_pixel * size) )

        self.cache_grid = [[None for i in range(len(self.grid[0]))] for i in range(len(self.grid))]
        self.cache_queue = []
        self.cache_queue_size = 20

    def download_image(self, i, j):
        filename = self.folder_name+"/"+str(i)+"-"+str(j)+".png"
        if os.path.exists(filename):
            return
        image_url = "https://maps.googleapis.com/maps/api/staticmap?"
        image_url += "center="+str(self.grid[i][j].lat)+","+str(self.grid[i][j].lng)
        image_url += "&zoom="+str(int(self.zoom))
        image_url += "&size="+str(self.size)+"x"+str(self.size)
        image_url += "&maptype=satellite&key=AIzaSyA7MIhe-OZEx4An2EQKAmVVwKCR6VMqQQA"
        r = requests.get(image_url)
        with open(filename,'wb') as f:
           f.write(r.content)

    def download_all(self):
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                self.download_image(i,j)

    def all_satellite_map(self):
        newimg = Image.new('RGB', (self.size * len(self.grid[0]), self.size * len(self.grid)))
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                filename = self.folder_name+"/"+str(i)+"-"+str(j)+".png"
                img = Image.open(filename)
                newimg.paste(img, (j * self.size, i * self.size))
        return newimg

    def average_filter(self,A):
        w = A.shape[0]
        h = A.shape[1]
        B = A.copy()
        for i in range(1,w-1):
            for j in range(1,h-1):
                B[i,j] =(A[i,j] + A[i-1,j] + A[i+1,j] + A[i,j-1] + A[i,j+1])/5
        return B

    def calc_vegetation_index(self, i, j):
        vi_filename = self.folder_name+"/vi/"+str(i)+"-"+str(j)+".png"
        if os.path.exists(vi_filename):
            return Image.open(vi_filename).convert('F')

        filename = self.folder_name+"/"+str(i)+"-"+str(j)+".png"
        r,g,b=Image.open(filename).convert("RGB").split()
        R = np.array(r)
        G = np.array(g)
        B = np.array(b)
        VI = np.zeros(R.shape)
        w = G.shape[0]
        h = G.shape[1]
        max_vi = 0
        for i in range(w):
            for j in range(h):
                if (int(G[i,j])-int(B[i,j]))<0 or (int(G[i,j])-int(R[i,j]))<0:
                    VI[i,j] = 0
                    continue
                VI[i,j] = (int(G[i,j])-int(R[i,j]))*(int(G[i,j])-int(B[i,j]))
                VI[i,j] = math.sqrt(VI[i,j])
                max_vi = max(max_vi, VI[i,j])
        VI = VI/max_vi*255
        viimg = Image.fromarray(self.average_filter(VI))
        viimg.convert('RGB').save(vi_filename)
        return viimg

    def get_vegetation_index_point(self, i, j, p, q):
        if 0 <= i and i < len(self.cache_grid) and 0 <= j and j < len(self.cache_grid[0]):
            if self.cache_grid[i][j] is None:
                self.tree_map_cache(i,j)
            if self.cache_grid[i][j] is not None and 0 <= p and p < self.size and 0 <= q and q < self.size:
                return self.cache_grid[i][j][p,q]
            else:
                return 0
        return 0

    def is_tree(self, lat, lng):
        r = 1
        t = self.get_vegetation_index_nearby(lat,lng,r)
        if np.sum(t) / 255 / ( (2*r+1)**2 ) > 0.1:
            return True
        return False

    def get_vegetation_index_nearby(self, lat, lng, r = 3):
        nearby = np.zeros((r*2+1,r*2+1))
        xy = latlng.LatLng(self.lat_N, self.lng_W).\
             get_latlng(-self.size*self.meters_per_pixel/2,self.size*self.meters_per_pixel/2).\
             get_xy(latlng.LatLng(lat, lng))
        if xy.x < 0 or xy.y > 0:
            return nearby
        i = int(-xy.y / self.meters_per_pixel / self.size)
        j = int( xy.x / self.meters_per_pixel / self.size)
        if i > len(self.grid) or i > len(self.grid[0]):
            return nearby
        p = int(-xy.y / self.meters_per_pixel) % self.size
        q = int( xy.x / self.meters_per_pixel) % self.size
        for pp in range(-r, r+1):
            for qq in range(-r, r+1):
                I = i
                J = j
                P = p + pp
                Q = q + qq
                if p + pp < 0:
                    I = i - 1
                    P = self.size + p + pp
                if q + qq < 0:
                    J = j - 1
                    Q = self.size + q + qq
                if p + pp >= self.size:
                    I = i + 1
                    P = p + pp - self.size
                if q + qq >= self.size:
                    J = j + 1
                    Q = q + qq - self.size
                nearby[pp + r][qq + r] = self.get_vegetation_index_point(I,J,P,Q)
        if r == 0:
            return nearby[0][0]
        return nearby

    def tree_map(self, i_range = None, j_range = None):
        newimg = Image.new('F', (self.size * len(self.grid[0]), self.size * len(self.grid)))
        if i_range is None: i_range = range(len(self.grid))
        if j_range is None: j_range = range(len(self.grid[0]))
        for i in i_range:
            for j in j_range:
                newimg.paste(self.calc_vegetation_index(i,j), (j * self.size, i * self.size))
        return newimg

    def tree_map_cache(self, i, j):
        if i < 0 or i >= len(self.grid) or j < 0 or j >= len(self.grid[0]):
            return
        self.cache_queue.append((i,j))
        self.cache_grid[i][j] = np.array(self.calc_vegetation_index(i,j).convert('F'))
        if len(self.cache_queue) > self.cache_queue_size:
            self.cache_grid[ self.cache_queue[0][0] ][ self.cache_queue[0][1] ] = None
            self.cache_queue.pop(0)
