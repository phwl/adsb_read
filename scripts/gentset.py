#!/home/phwl/anaconda3/bin/python
import pickle
import numpy as np
import os
import re
import math
import pyModeS as pms
from ADSBwave import *

def readdir(dir):
    wave = ADSBwave(osr=4)
    fsize = 0
    verified = 0
    dataset = []
    dirfiles = os.listdir(dir)
    dirfiles.sort(key=lambda f: int(re.sub('\D', '', f)))
    for filename in dirfiles:
        if filename.endswith(".bin"):
            fname = (os.path.join(dir, filename))
            fsize += os.path.getsize(fname)
            with open(fname, 'rb') as f:
               data = pickle.load(f)
               dataset = dataset + data
               print('file:', fname, len(data), len(dataset))
               for x in data:
                   (dtime, d_in, d_out) = x
                   print(dtime)
                   try:
                       pms.tell(d_out)
                       v = wave.verify(d_in, d_out)
                       if v:
                           verified += 1
                   except:
                       #import pdb; pdb.set_trace()
                       print('Verify FAILED')
                       pass
                   print()
    print("Total records=", len(dataset), 'verified=', verified)
    print("Total file size", eng_string(fsize, si=True))
    return dataset

def writedata(fname, dataset):
    print("Writing training file to", fname)
    with open(fname, "wb") as fd:
        pickle.dump(dataset, fd)

if __name__ == "__main__":
    dir='/srv/breamdisk/adsb-data/'
    fname = 'tdata.bin'
    dataset = readdir(dir)
    # writedata(fname, dataset)
