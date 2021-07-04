#!/home/phwl/anaconda3/bin/python
import pickle
import numpy as np
import os
import re
import math
import pyModeS as pms
from ADSBwave import *

def eng_string( x, format='%s', si=False):
    '''
    Returns float/int value <x> formatted in a simplified engineering format -
    using an exponent that is a multiple of 3.

    format: printf-style string used to format the value before the exponent.

    si: if true, use SI suffix for exponent, e.g. k instead of e3, n instead of
    e-9 etc.

    E.g. with format='%.2f':
        1.23e-08 => 12.30e-9
             123 => 123.00
          1230.0 => 1.23e3
      -1230000.0 => -1.23e6

    and with si=True:
          1230.0 => 1.23k
      -1230000.0 => -1.23M
    '''
    sign = ''
    if x < 0:
        x = -x
        sign = '-'
    exp = int( math.floor( math.log10( x)))
    exp3 = exp - ( exp % 3)
    x3 = x / ( 10 ** exp3)

    if si and exp3 >= -24 and exp3 <= 24 and exp3 != 0:
        exp3_text = 'yzafpnum kMGTPEZY'[ ( exp3 - (-24)) // 3]
    elif exp3 == 0:
        exp3_text = ''
    else:
        exp3_text = 'e%s' % exp3

    return ( '%s'+format+'%s') % ( sign, x3, exp3_text)

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
    writedata(fname, dataset)
