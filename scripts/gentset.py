#!/usr/bin/python3

# generate a test set for NN training

import pickle
import numpy as np
import os, gc
import re
import math
import pyModeS as pms
from ADSBwave import *
import pdb

def mytell(msg, lfp):
    from pyModeS import common, adsb, commb, bds

    def _print(label, value, unit=None):
        print("%20s: " % label, end="", file=lfp)
        print("%s " % value, end="", file=lfp)
        if unit:
            print(unit, file=lfp)
        else:
            print(file=lfp)

    df = common.df(msg)
    icao = common.icao(msg)

    _print("Message", msg)
    _print("ICAO address", icao)
    _print("Downlink Format", df)

    if df == 17:
        _print("Protocol", "Mode-S Extended Squitter (ADS-B)")

        tc = common.typecode(msg)
        if 1 <= tc <= 4:  # callsign
            callsign = adsb.callsign(msg)
            _print("Type", "Identitification and category")
            _print("Callsign:", callsign)

        if 5 <= tc <= 8:  # surface position
            _print("Type", "Surface position")
            oe = adsb.oe_flag(msg)
            msgbin = common.hex2bin(msg)
            cprlat = common.bin2int(msgbin[54:71]) / 131072.0
            cprlon = common.bin2int(msgbin[71:88]) / 131072.0
            v = adsb.surface_velocity(msg)
            _print("CPR format", "Odd" if oe else "Even")
            _print("CPR Latitude", cprlat)
            _print("CPR Longitude", cprlon)
            _print("Speed", v[0], "knots")
            _print("Track", v[1], "degrees")

        if 9 <= tc <= 18:  # airborne position
            _print("Type", "Airborne position (with barometric altitude)")
            alt = adsb.altitude(msg)
            oe = adsb.oe_flag(msg)
            msgbin = common.hex2bin(msg)
            cprlat = common.bin2int(msgbin[54:71]) / 131072.0
            cprlon = common.bin2int(msgbin[71:88]) / 131072.0
            _print("CPR format", "Odd" if oe else "Even")
            _print("CPR Latitude", cprlat)
            _print("CPR Longitude", cprlon)
            _print("Altitude", alt, "feet")

        if tc == 19:
            _print("Type", "Airborne velocity")
            spd, trk, vr, t = adsb.velocity(msg)
            types = {"GS": "Ground speed", "TAS": "True airspeed"}
            _print("Speed", spd, "knots")
            _print("Track", trk, "degrees")
            _print("Vertical rate", vr, "feet/minute")
            _print("Type", types[t])

        if 20 <= tc <= 22:  # airborne position
            _print("Type", "Airborne position (with GNSS altitude)")
            alt = adsb.altitude(msg)
            oe = adsb.oe_flag(msg)
            msgbin = common.hex2bin(msg)
            cprlat = common.bin2int(msgbin[54:71]) / 131072.0
            cprlon = common.bin2int(msgbin[71:88]) / 131072.0
            _print("CPR format", "Odd" if oe else "Even")
            _print("CPR Latitude", cprlat)
            _print("CPR Longitude", cprlon)
            _print("Altitude", alt, "feet")

    if df == 20:
        _print("Protocol", "Mode-S Comm-B altitude reply")
        _print("Altitude", common.altcode(msg), "feet")

    if df == 21:
        _print("Protocol", "Mode-S Comm-B identity reply")
        _print("Squawk code", common.idcode(msg))

    if df == 20 or df == 21:
        labels = {
            "BDS10": "Data link capability",
            "BDS17": "GICB capability",
            "BDS20": "Aircraft identification",
            "BDS30": "ACAS resolution",
            "BDS40": "Vertical intention report",
            "BDS50": "Track and turn report",
            "BDS60": "Heading and speed report",
            "BDS44": "Meteorological routine air report",
            "BDS45": "Meteorological hazard report",
            "EMPTY": "[No information available]",
        }

        BDS = bds.infer(msg, mrar=True)
        if BDS in labels.keys():
            _print("BDS", "%s (%s)" % (BDS, labels[BDS]))
        else:
            _print("BDS", BDS)

        if BDS == "BDS20":
            callsign = commb.cs20(msg)
            _print("Callsign", callsign)

        if BDS == "BDS40":
            _print("MCP target alt", commb.selalt40mcp(msg), "feet")
            _print("FMS Target alt", commb.selalt40fms(msg), "feet")
            _print("Pressure", commb.p40baro(msg), "millibar")

        if BDS == "BDS50":
            _print("Roll angle", commb.roll50(msg), "degrees")
            _print("Track angle", commb.trk50(msg), "degrees")
            _print("Track rate", commb.rtrk50(msg), "degree/second")
            _print("Ground speed", commb.gs50(msg), "knots")
            _print("True airspeed", commb.tas50(msg), "knots")

        if BDS == "BDS60":
            _print("Megnatic Heading", commb.hdg60(msg), "degrees")
            _print("Indicated airspeed", commb.ias60(msg), "knots")
            _print("Mach number", commb.mach60(msg))
            _print("Vertical rate (Baro)", commb.vr60baro(msg), "feet/minute")
            _print("Vertical rate (INS)", commb.vr60ins(msg), "feet/minute")

        if BDS == "BDS44":
            _print("Wind speed", commb.wind44(msg)[0], "knots")
            _print("Wind direction", commb.wind44(msg)[1], "degrees")
            _print("Temperature 1", commb.temp44(msg)[0], "Celsius")
            _print("Temperature 2", commb.temp44(msg)[1], "Celsius")
            _print("Pressure", commb.p44(msg), "hPa")
            _print("Humidity", commb.hum44(msg), "%")
            _print("Turbulence", commb.turb44(msg))

        if BDS == "BDS45":
            _print("Turbulence", commb.turb45(msg))
            _print("Wind shear", commb.ws45(msg))
            _print("Microbust", commb.mb45(msg))
            _print("Icing", commb.ic45(msg))
            _print("Wake vortex", commb.wv45(msg))
            _print("Temperature", commb.temp45(msg), "Celsius")
            _print("Pressure", commb.p45(msg), "hPa")
            _print("Radio height", commb.rh45(msg), "feet")

# read and decode all .bin files in the directory, 
def readdir(dir, lfp, verbose=0, osr=4, wave=None):
    if wave is None:
        wave = ADSBwave(osr=osr, verbose=verbose, lfp=lfp)
        
    fsize = 0

    fcount = 0
    verified = 0
    failed = 0
    dataset = []
    print(f"Exploring Directory: {dir}:", file=lfp)
    dirfiles = os.listdir(dir)
    #dirfiles.sort(key=lambda f: int(re.sub('\D', '', f)))
    dirfiles_sorted = sorted(dirfiles)

    for filename in dirfiles_sorted:
        if filename.endswith(".bin"):            
            fcount += 1            
            fname = (os.path.join(dir, filename))
            fsize += os.path.getsize(fname)
            with open(fname, 'rb') as f:
                data = pickle.load(f)
                print(f"file({fcount}): {fname} {len(data)} {len(dataset)}", file=lfp)
                fstr = f"file({fcount}): {fname} {len(data)} {len(dataset)}"
                valid_data = []
                for x in data:
                    (dtime, d_in, d_out) = x
                    if verbose > 0:
                        print(dtime, file=lfp)
                    v = wave.verify(d_in, d_out)
                    if v:
                        verified += 1
                        valid_data.append((dtime, d_in, d_out))
                    else:
                        failed += 1
                        
                    try:
                        #pms.tell(d_out)
                        if verbose > 0:
                            mytell(d_out, lfp)
                        pass    
                    except:
                        #import pdb; pdb.set_trace()
                        pass
                        
                    if verbose > 0:
                        print(file=lfp)
                    
                    print(f"\r{fstr} - Verified: {verified}, Failed: {failed}        ", end='')

                dataset = dataset + valid_data

    print(f"\nFound {fcount} .bin files in {dir}")
    print(f"Total records={len(dataset)} verified={verified} failed={failed}")
    print(f"Total file size {eng_string(fsize, format='%.3f', si=True)}")

    print(f"\nFound {fcount} .bin files in {dir}", file=lfp)
    print(f"Total records={len(dataset)} verified={verified} failed={failed}", file=lfp)
    print(f"Total file size {eng_string(fsize, format='%.3f', si=True)}", file=lfp, flush=True)

    return dataset, fcount

# call readdir for all subdirectories of rootdir
def dirwalk(rootdir, lfp, verbose=0, osr=4, save_by_dir=None):

    wave = ADSBwave(osr=osr, verbose=verbose, lfp=lfp)
    fcount = 0
    
    dataset = []
    for dirname in os.listdir(rootdir):
        print(f"Checking: {dirname} in {rootdir}", file=lfp)
        if os.path.isdir(f"{rootdir}/{dirname}"):
            print(f"reading from: {dirname} in {rootdir}", file=lfp)
            r_dataset, r_fcount = readdir(f"{rootdir}/{dirname}", lfp, verbose=verbose, osr=osr, wave=wave)
            
            if save_by_dir is None:
                print(f"Appending dataset: {rootdir}", file=lfp, flush=True)
                dataset += r_dataset
            elif len(r_dataset) > 0:
                fname = f"{save_by_dir}_{dirname}.bin"
                writedata(fname, lfp, r_dataset)  
                
                # Force GC
                r_dataset = None
                gc.collect()
                
            fcount += r_fcount

    print(f"reading from: {rootdir}", file=lfp)
    r_dataset, r_fcount = readdir(rootdir, lfp, verbose=verbose, osr=osr, wave=wave)
    fcount += r_fcount
    print(f"Total of {fcount} records read.", file=lfp, flush=True)

    if save_by_dir is None:
        print(f"Appending dataset: {rootdir}", file=lfp, flush=True)
        dataset += r_dataset

        return dataset
        
    elif len(r_dataset) > 0:
        fname = f"{save_by_dir}_{rootdir}.bin"
        writedata(fname, lfp, r_dataset)  
        
        return
                
# write dataset to a file 
def writedata(fname, lfp, dataset, trunc=None):

    if trunc is None:
        print(f"Saving data to: {fname}.", file=lfp, flush=True)
        print(f"Saving data to: {fname}.", flush=True)
        with open(fname, "wb") as fd:
            pickle.dump(dataset, fd)
    else:
        print(f"Saving truncated data to: {fname}.", file=lfp, flush=True)
        print(f"Saving truncated data to: {fname}.", flush=True)
        with open(fname, "wb") as fd:
            pickle.dump(dataset[:trunc], fd)

    fsize = os.path.getsize(fname)
    print(f"Wrote training file of size {eng_string(fsize, format='%.3f', si=True)} to {fname}.", file=lfp, flush=True)
    print(f"Wrote training file of size {eng_string(fsize, format='%.3f', si=True)} to {fname}.", flush=True)
    
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Verbose mode')
    parser.add_argument('-d', '--dirname', type=str, default='.', help='Root directory wherre to find the raw adsb data files in .bin format')
    parser.add_argument('--osr', action='store', type=int, default=4,
                        help='Over-Sampling Rate')
    parser.add_argument('--trunc', action='store', type=int, default=None,
                    help='Truncate the output to create a shiorter file for debugging')

    parser.add_argument('-D', '--save_by_dir', action='store_true', default=False,
                        help='Save data by directory name in which they are found')

    parser.add_argument('-w', '--write', action='store_true', default=False,
                        help='Write out validate data to ONAME')
    parser.add_argument('--oname', action='store', type=str, default='tdata.bin',
                        help='Output file name')
    parser.add_argument('--logfile', action='store', type=str, default='gentset.log',
                        help='Output file name')
    cargs = parser.parse_args()

    with open(cargs.logfile, 'w') as lfp:
        if cargs.save_by_dir:
            sbd = cargs.oname
            dirwalk(cargs.dirname, lfp, verbose=cargs.verbose, osr=cargs.osr, save_by_dir=sbd)        
        else:
            dataset = dirwalk(cargs.dirname, lfp, verbose=cargs.verbose, osr=cargs.osr)
            if cargs.write:
                writedata(cargs.oname, lfp, dataset, cargs.trunc)

        print(f"Completed OK!", file=lfp, flush=True)
        
    print(f"Completed OK.", flush=True)
    
    exit(0)
    
