import sys
sys.path.append("py")

import roadnetwork
import treefinder
import simulator
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    s = simulator.Simulator()
    s.run(21600)
    s.plot()
