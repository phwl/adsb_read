#!/usr/bin/python3

# generate a test set for NN training

import pickle
import shutil
import numpy as np
import os
import re
import math
import pyModeS as pms
from ADSBwave import *
import pdb

def mkdircp(src, dstdir, dirname, ex=True):
    dstdir = dstdir + '/' + dirname
    if not os.path.isdir(dstdir):
        print('os.mkdir({})'.format(dstdir))
        if ex:
            os.mkdir(dstdir)
    print('cp {} {}\n'.format(src, dstdir))
    print('shutil.copy2(src, dstdir)'.format(src, dstdir)) 
    if ex:
        shutil.copy2(src, dstdir)

# read and decode all .bin files in the directory, 
def readdir(srcdir, dstdir, verbose=0, osr=4):
    wave = ADSBwave(osr=osr, verbose=verbose)
    fsize = 0
    fcount = 0
    verified = 0
    failed = 0
    dataset = []
    dirfiles = os.listdir(srcdir)
    dirfiles.sort(key=lambda f: int(re.sub('\D', '', f)))
    # dirfiles_sorted = sorted(dirfiles)

    for filename in dirfiles:
        if filename.endswith(".bin"):
            fcount += 1
            fname = (os.path.join(srcdir, filename))
            mtime = os.path.getmtime(fname)
            xctime = time.strftime("%Y-%m-%d", time.localtime(mtime))
            mkdircp(fname, dstdir, '{}'.format(xctime))

# call readdir for all subdirectories of rootdir
def dirwalk(rootdir, dstdir, verbose=0, osr=4):

    dataset = []
    for dirname in os.listdir(rootdir):
        print('* {}'.format(dirname))
        if os.path.isdir(f"{rootdir}/{dirname}"):
            print(f"reading from: {dirname} in {rootdir}")
            readdir(f"{rootdir}/{dirname}", dstdir, verbose=verbose, osr=osr)
    return dataset
                
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Verbose mode')
    parser.add_argument('-s', '--srcdir', type=str, default='.', help='Root directory where to find the raw adsb data files in .bin format')
    parser.add_argument('-d', '--dstdir', type=str, default='/tmp', help='Root directory where to place the raw adsb data files in .bin format')
    parser.add_argument('--osr', action='store', type=int, default=4,
                        help='Over-Sampling Rate')
    cargs = parser.parse_args()

    dataset = dirwalk(cargs.srcdir, cargs.dstdir, verbose=cargs.verbose, osr=cargs.osr)
    
    exit(0)
    
