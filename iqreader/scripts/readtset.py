import pickle
import numpy as np
import os

dir='/srv/breamdisk/adsb-data/'
dataset = []
for filename in os.listdir(dir):
    if filename.endswith(".bin"):
        fname = (os.path.join(dir, filename))
        with open(fname, 'rb') as f:
           data = pickle.load(f)
           print(data[0][0])
           dataset = dataset + data
           print(fname, len(data), len(dataset))

fname = 'tdata.bin'
print("Writing training file to", fname)
with open(fname, "wb") as fd:
    pickle.dump(dataset, fd)
