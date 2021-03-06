#!/usr/bin/python3

# generate a test set for NN training

import pickle, h5py
import numpy as np
import os, gc
import re
import math
import pyModeS as pms
from ADSBwave import *

cruxml_dnn_path = '../../CruxML_DNN'
if os.path.isdir(cruxml_dnn_path):
    sys.path.append(cruxml_dnn_path)
else:
    print(f"ERROR: {cruxml_dnn_path} path not found, please instal CruxML_DNN from git repo!")
    exit(3)
    
import utils.adsb_decoder as adsb_dec
from tqdm import tqdm
from pathlib import Path
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
    # Set to positive integer for debugging.
    ftrunc = 0

    for filename in dirfiles_sorted:
        if ftrunc > 0 and fcount > ftrunc:
            break
        if filename.endswith(".bin"):            
            fcount += 1            
            fname = (os.path.join(dir, filename))
            fsize += os.path.getsize(fname)
            with open(fname, 'rb') as f:
                data = pickle.load(f)
                if verbose > 1:
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
def dirwalk_old(rootdir, lfp, cargs):

    wave = ADSBwave(osr=cargs.osr, verbose=cargs.verbose, lfp=lfp)
    fcount = 0

    if cargs.preproc:
        icao_to_label_map = []

    dataset = []
        
    for dirname in os.listdir(rootdir):
        print(f"Checking: {dirname} in {rootdir}", file=lfp)
        if os.path.isdir(f"{rootdir}/{dirname}"):
            print(f"reading from: {dirname} in {rootdir}", file=lfp)
            r_dataset, r_fcount = readdir(f"{rootdir}/{dirname}", lfp, verbose=cargs.verbose, osr=cargs.osr, wave=wave)
                       
            if not cargs.save_by_dir or cargs.agg:
                if not cargs.preproc:
                    print(f"Appending dataset: {rootdir}", file=lfp, flush=True)
                    dataset += r_dataset
                    
                else:
                    sei_timestamps, sei_inputs, sei_inputs_iq, sei_labels = preproc_sei_raw(lfp, cargs, r_dataset, icao_to_label_map)
                    if sei_timestamps is not None and sei_timestamps.shape[0] > 0:
                        print(f"Samples: {len(sei_timestamps)}", file=lfp, flush=True)
                        print(f"icao_to_label_map len: {len(icao_to_label_map)}", file=lfp, flush=True)
                        dataset.append([sei_timestamps, sei_inputs, sei_inputs_iq, sei_labels])
                    else:
                        print(f"Samples: 0", file=lfp, flush=True)
                        
            elif len(r_dataset) > 0:
                fname = f"{cargs.oname}_{dirname}.{cargs.otype}"
                writedata(cargs, fname, lfp, r_dataset)  
                
                # Force GC
                r_dataset = None
                gc.collect()
                
            fcount += r_fcount
            print(f"Subtotal of {r_fcount} records read.", file=lfp, flush=True)

    print(f"reading from: {rootdir}", file=lfp)
    r_dataset, r_fcount = readdir(rootdir, lfp, verbose=cargs.verbose, osr=cargs.osr, wave=wave)
    fcount += r_fcount
    print(f"Total of {fcount} records read.", file=lfp, flush=True)

    if not cargs.save_by_dir or cargs.agg:
        if not cargs.preproc:
            print(f"Appending dataset: {rootdir}", file=lfp, flush=True)
            dataset += r_dataset
            
            return dataset, None, False
            
        else:
            sei_timestamps, sei_inputs, sei_inputs_iq, sei_labels = preproc_sei_raw(lfp, cargs, r_dataset, icao_to_label_map)
            if sei_timestamps is not None and sei_timestamps.shape[0] > 0:
                print(f"Sample len: {len(sei_timestamps)}", file=lfp, flush=True)
                print(f"icao_to_label_map len: {len(icao_to_label_map)}", file=lfp, flush=True)
                dataset.append([sei_timestamps, sei_inputs, sei_inputs_iq, sei_labels])
            else:
                print(f"Samples: 0", file=lfp, flush=True)
        
            return dataset, icao_to_label_map, True
                            
    elif len(r_dataset) > 0:
        fname = f"{cargs.oname}_{rootdir}.{cargs.otype}"
        writedata(cargs, fname, lfp, r_dataset)  
        
    return None, None

# call readdir for all subdirectories of rootdir
def dirwalk(rootdir, lfp, cargs):

    wave = ADSBwave(osr=cargs.osr, verbose=cargs.verbose, lfp=lfp)
    fcount = 0

    if cargs.preproc:
        icao_to_label_map = []

    dataset = []

    if isinstance(rootdir, list):
        dir_list = rootdir
    else:
        dir_list = [rootdir]
        
    for dirname in rootdir:
        fcount += dir_read_and_walk(lfp, cargs, dirname, dataset, icao_to_label_map, dirname, wave)

    print(f"Total of {fcount} records read.", file=lfp, flush=True)

    if not cargs.save_by_dir or cargs.agg:
        if not cargs.preproc:           
            return dataset, None, False
            
        else:        
            return dataset, icao_to_label_map, True
                            
    else:     
        return None, None, None
   
def dir_read_and_walk(lfp, cargs, dirname_path, dataset, icao_to_label_map, rootdir, wave):

    r_fcount = 0
    # Descend through child directories
    for subdirname in os.listdir(dirname_path):
        subdirname_path = f"{dirname_path}/{subdirname}"
        print(f"Checking: {dirname_path} in {subdirname}", file=lfp)
        if os.path.isdir(subdirname_path):
            r_fcount += dir_read_and_walk(lfp, cargs, subdirname_path, dataset, icao_to_label_map, rootdir, wave)
    
    # Process files in this directory    
    print(f"reading from: {dirname_path}", file=lfp)
    r_dataset, l_r_fcount = readdir(dirname_path, lfp, verbose=cargs.verbose, osr=cargs.osr, wave=wave)
                       
    if not cargs.save_by_dir or cargs.agg:
        if not cargs.preproc:
            print(f"Appending dataset: {rootdir}", file=lfp, flush=True)
            dataset += r_dataset
            
        else:
            sei_timestamps, sei_inputs, sei_inputs_iq, sei_labels = preproc_sei_raw(lfp, cargs, r_dataset, icao_to_label_map)
            if sei_timestamps is not None and sei_timestamps.shape[0] > 0:
                print(f"Samples: {len(sei_timestamps)}", file=lfp, flush=True)
                print(f"icao_to_label_map len: {len(icao_to_label_map)}", file=lfp, flush=True)
                dataset.append([sei_timestamps, sei_inputs, sei_inputs_iq, sei_labels])
            else:
                print(f"Samples: 0", file=lfp, flush=True)
                
    elif len(r_dataset) > 0:
        fname = f"{cargs.oname}_{dirname_path.replace(rootdir,'')}.{cargs.otype}"
        writedata(cargs, fname, lfp, r_dataset)  
        
        # Force GC
        r_dataset = None
        gc.collect()
        
    fcount = r_fcount + l_r_fcount
    print(f"Subtotal of {fcount} records read.", file=lfp, flush=True)
        
    return fcount

def get_class_stats(arr):
    class_stats = {}
    class_stats['values'], class_stats['counts'] = np.unique(arr, return_counts=True)
    
    return class_stats

def filter_classes(cargs, lfp, sei_labels, sei_inputs, sei_inputs_iq, sei_timestamps, icao_to_label_map):

    class_stats = get_class_stats(sei_labels)
    csv, csc = class_stats['values'], class_stats['counts']
    inc_labels_idxs = []
    for c_id in range(csc.shape[0]):
        if csc[c_id] >= cargs.class_sample_thresh:
            inc_labels_idxs.extend(np.where(sei_labels == csv[c_id])[0].tolist())

    inc_labels_count = len(inc_labels_idxs)
    print(f"found {inc_labels_count} classes with sample count >= {cargs.class_sample_thresh} out of {csc.shape[0]} original classes.", file=lfp, flush=True)
    if inc_labels_count > 0:
        print(f"maximum sample count = {csc.max()}.", file=lfp, flush=True)
    
    #if inc_labels_count > 1:
    #    inc_labels_idxs = np.concatenate(inc_labels)
    #elif inc_labels_count == 1:
    #    inc_labels_idxs = inc_labels
    #else:
    if inc_labels_count < 1:
        print(f"WARNING: No classes found with sample count >= {cargs.class_sample_thresh}", file=lfp, flush=True)
        #exit(2)
        return None, None, None, None, None, None
    
    r_sei_labels = sei_labels[inc_labels_idxs]
    r_sei_inputs = sei_inputs[inc_labels_idxs]
    r_sei_inputs_iq = sei_inputs_iq[inc_labels_idxs]
    r_sei_timestamps = sei_timestamps[inc_labels_idxs]
    samples_num = r_sei_labels.shape[0]

    # Regenerate labels
    new_unique_labels = np.unique(sei_labels)
    sei_label_num = new_unique_labels.shape[0]
    new_icao_to_label_map = []
    for new_lbl, old_lbl in enumerate(new_unique_labels):
        sei_labels[sei_labels==old_lbl] = new_lbl
        new_icao_to_label_map.append(icao_to_label_map[old_lbl])

    # Regenerate Class stats
    class_stats = get_class_stats(r_sei_labels)
    assert class_stats['counts'].sum() == samples_num

    return r_sei_labels , r_sei_inputs, r_sei_inputs_iq, r_sei_timestamps, new_icao_to_label_map, samples_num
        
def preproc_sei_raw(lfp, cargs, dataset, icao_to_label_map):
    ''' Preprocess Raw SEI data which is in the form of a list of  tuples (dtime, d_in, d_out)
    where:
        dtime is the timestamp
        d_in is a numpy array of complex
        dount is a hexidecimal stream
    '''

    samples_num = len(dataset)

    # SEI Input is real pairs as the real part and the magnitde of the complex part.
    # Only first preamble samples are used

    sample_rate = cargs.raw_sample_rate * cargs.over_sample
    preamble_sample_num = int(cargs.preamble_time * sample_rate)
    psn = preamble_sample_num
    in_size = int(psn*2)

    if samples_num < 1:
        print(f"No data found for preprocessing!", file=lfp, flush=True)
        #sei_inputs_iq = np.ndarray((samples_num, psn)).astype(np.complex128)        
        #sei_inputs = np.ndarray((samples_num, in_size)).astype(np.float64)        
        #sei_timestamps = np.ndarray((samples_num, psn)).astype(np.float64)        
        #sei_labels = np.zeros((samples_num)).astype(np.int32)

        return None, None, None, None

    print(f"Preprocessing Raw Input data with preamble_sample_num: {preamble_sample_num}", file=lfp, flush=True)
    print(f"Raw Input data len: {samples_num}, and raw input type is: {type(dataset[0])} of length {len(dataset[0])}", file=lfp, flush=True)
    
    # Acquire samples and labels (also provide raw I/Q samples)
    sei_inputs_iq = np.ndarray((samples_num, psn)).astype(np.complex128)        
    sei_inputs = np.ndarray((samples_num, in_size)).astype(np.float64)        
    sei_timestamps = np.ndarray((samples_num)).astype(np.float64)        
    sei_labels = np.zeros((samples_num)).astype(np.int32)
    
    # Accummuate Unique Ids
    #icao_to_label_map = []
    icao_to_label_num = len(icao_to_label_map)
    samples_with_icao = 0
    np_julian_zero = np.datetime64('1970-01-01T00:00:00')
    np_1sec = np.timedelta64(1, 's')
    df_stats = {}
    
    for dtuple in tqdm(dataset, desc="Extract from RAW SEI"):
        dtime, d_in, d_out = dtuple
        
        # Get unique ID part of ADBS code
        icao_addr, df_val = adsb_dec.get_icao(d_out)
        if df_val in df_stats:
            df_stats[df_val] += 1
        else:
            df_stats[df_val] = 1
            
        if icao_addr is None:
            continue
            
        try:
            sei_label = icao_to_label_map.index(icao_addr)
            
        except ValueError:
            print(f"Adding new icao_addr: {icao_addr} as id: {icao_to_label_num} to icao_to_label_map", file=lfp, flush=True)
            icao_to_label_map.append(icao_addr)
            icao_to_label_num += 1
            sei_label = icao_to_label_map.index(icao_addr)
             
        sei_labels[samples_with_icao] = sei_label
        np_d_in = np.array(d_in)
        # Convert to Real and Imaginary parts else use Magnitude and phase
        if cargs.real_im:
            sei_inputs[samples_with_icao] = np.concatenate((np.real(np_d_in[0:psn]),np.imag(np_d_in[0:psn])))
        else:  
            sei_inputs[samples_with_icao] = np.concatenate((np.abs(np_d_in[0:psn]),np.angle(np_d_in[0:psn])))

        sei_inputs_iq[samples_with_icao] = np_d_in[0:psn]
        sei_timestamps[samples_with_icao] = (np.datetime64(dtime) - np_julian_zero) / np_1sec
        samples_with_icao += 1

    print(f"DF stats.", file=lfp, flush=True)
    for k in df_stats.keys():
        print(f"   {k}: {df_stats[k]}", file=lfp, flush=True)
    
    # truncate dataset to those with valid callsign_to_label_map
    print(f"Got {samples_with_icao} samples with valid icao and {icao_to_label_num} distinct icaos.", file=lfp, flush=True)
    sei_inputs = sei_inputs[:samples_with_icao,:]
    sei_inputs_iq = sei_inputs_iq[:samples_with_icao,:]
    sei_timestamps = sei_timestamps[:samples_with_icao]
    sei_labels = sei_labels[:samples_with_icao]
    samples_num = samples_with_icao

    sei_label_num = icao_to_label_num

    # Now filter out classes with insufficient samples if requested
    if cargs.class_sample_thresh > 0:
        sei_labels, sei_inputs, sei_inputs_iq, sei_timestamps, icao_to_label_map, samples_num = filter_classes(cargs, lfp, sei_labels, sei_inputs, sei_inputs_iq, sei_timestamps, icao_to_label_map)
                
    return sei_timestamps, sei_inputs, sei_inputs_iq, sei_labels
    
# write dataset to a file starting from unpreprocessed data 
def writedata(cargs, fname, lfp, dataset, icao_to_label_map_in=None, preproced=False):
    SEIdata_version = '1.0'

    if cargs.trunc is None:
        tstr = ""
        s_dset = dataset
    else:
        tstr = " truncated"
        s_dset = dataset[:cargs.trunc]

    if cargs.preproc:

        if preproced:
            icao_to_label_map = icao_to_label_map_in
            
            if len(s_dset) == 0:
                print(f"No data to save!", file=lfp, flush=True)
                return
            else:
                ts_lst = []
                in_lst = []
                in_iq_lst = []
                lbls_lst = []
                for s_d in s_dset:
                    ts_lst.append(s_d[0])
                    in_lst.append(s_d[1])
                    in_iq_lst.append(s_d[2])
                    lbls_lst.append(s_d[3])

                sei_timestamps = np.concatenate(ts_lst)
                sei_inputs = np.concatenate(in_lst)
                sei_inputs_iq = np.concatenate(in_iq_lst)
                sei_labels = np.concatenate(lbls_lst)
        else:
            icao_to_label_map = []
            sei_timestamps, sei_inputs, sei_inputs_iq, sei_labels = preproc_sei_raw(lfp, cargs, s_dset, icao_to_label_map)

        samples_num = sei_timestamps.shape[0] 

        print(f"ICAO Stats", file=lfp, flush=True)
        icao_labels, cnts = np.unique(sei_labels, return_counts=True)
        for icao_label, cnt in zip(icao_labels, cnts):
            print(f"{icao_label}: {icao_to_label_map[icao_label]}, samples: {cnt}.", file=lfp, flush=True)
            
        if samples_num > 0:
            print(f"Saving preprocessed data of {samples_num} samples to: {fname}.", file=lfp, flush=True)
            print(f"Saving preprocessed data of {samples_num} samples to: {fname}.", flush=True)
                
            if ".h5" in fname:
                with h5py.File(fname, 'w') as data_file:
                    data_file.create_dataset('sei_timestamps', data=sei_timestamps)
                    data_file.create_dataset('sei_inputs', data=sei_inputs)
                    data_file.create_dataset('sei_inputs_iq', data=sei_inputs_iq)
                    data_file.create_dataset('sei_labels', data=sei_labels)
                    data_file.create_dataset('icao_to_label_map', data=icao_to_label_map)
                    data_file.attrs['SEIData_version'] = SEIdata_version
        else:
            print(f"No valid samples found for saving!", file=lfp, flush=True)
            print(f"No valid samples found for saving!", flush=True)
            
    else:

        print(f"Saving{tstr} data to: {fname}.", file=lfp, flush=True)
        print(f"Saving{tstr} data to: {fname}.", flush=True)

        # Ensure the parent directory exists
        parent = Path(fname).resolve().parent
        parent.mkdir(parents=True, exist_ok=True)
        
        if ".h5" in fname:
            with h5py.File(fname, 'w') as data_file:
                data_file.create_dataset('timestamp', data=s_dset[0])
                data_file.create_dataset('d_in', data=s_dset[1])
                data_file.create_dataset('d_out', data=s_dset[2])
        
        elif '.bin' in fname:
            with open(fname, "wb") as fd:
                pickle.dump(s_dset, fd)

    fsize = os.path.getsize(fname)
    print(f"Wrote training file of size {eng_string(fsize, format='%.3f', si=True)} to {fname}.", file=lfp, flush=True)
    print(f"Wrote training file of size {eng_string(fsize, format='%.3f', si=True)} to {fname}.", flush=True)

# write dataset to a file starting from preprocessed data 
def writedata_old(cargs, fname, lfp, dataset, icao_to_label_map):

    sei_timestamps = []
    sei_inputs = []
    sei_inputs_iq = []
    sei_labels = []
    for dsi in dataset:
        sei_timestamps.append(dsi[0])
        sei_inputs.append(dsi[1])
        sei_inputs_iq.append(dsi[2])
        sei_labels.append(dsi[3])

    sei_timestamps = np.concatenate(sei_timestamps, axis=0)
    sei_inputs = np.concatenate(sei_inputs, axis=0)
    sei_inputs_iq = np.concatenate(sei_inputs_iq, axis=0)
    sei_labels = np.concatenate(sei_labels, axis=0)
        
    samples_num = sei_inputs.shape[0]

    sei_labels, sei_inputs, sei_inputs_iq, sei_timestamps, icao_to_label_map, samples_num = filter_classes(cargs, lfp, sei_labels, sei_inputs, sei_inputs_iq, sei_timestamps, icao_to_label_map)
        
    if samples_num > 0:
        if ".h5" not in fname:
            print(f"Forcing data type to H5!", file=lfp, flush=True)
            print(f"Forcing data type to H5!", flush=True)
            fname += '.h5'
            
        print(f"Saving preprocessed data of {samples_num} samples to: {fname}.", file=lfp, flush=True)
        print(f"Saving preprocessed data of {samples_num} samples to: {fname}.", flush=True)
            
        with h5py.File(fname, 'w') as data_file:
            data_file.create_dataset('sei_timestamps', data=sei_timestamps)
            data_file.create_dataset('sei_inputs', data=sei_inputs)
            data_file.create_dataset('sei_inputs_iq', data=sei_inputs_iq)
            data_file.create_dataset('sei_labels', data=sei_labels)
            data_file.create_dataset('icao_to_label_map', data=icao_to_label_map)

        
    else:
        print(f"No valid samples found for saving!", file=lfp, flush=True)
        print(f"No valid samples found for saving!", flush=True)
            

    fsize = os.path.getsize(fname)
    print(f"Wrote training file of size {eng_string(fsize, format='%.3f', si=True)} to {fname}.", file=lfp, flush=True)
    print(f"Wrote training file of size {eng_string(fsize, format='%.3f', si=True)} to {fname}.", flush=True)
    
    
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Verbose mode')
    parser.add_argument('-d', '--dirname', nargs='+', type=str, default='.', help='Root directory wherre to find the raw adsb data files in .bin format')
    parser.add_argument('--osr', action='store', type=int, default=4, help='Over-Sampling Rate')
    parser.add_argument('--trunc', action='store', type=int, default=None, help='Truncate the output to create a shiorter file for debugging')

    parser.add_argument('-D', '--save_by_dir', action='store_true', default=False, help='Save data by directory name in which they are found')

    parser.add_argument('-w', '--write', action='store_true', default=False, help='Write out validate data to ONAME')
    parser.add_argument('--oname', action='store', type=str, default='tdata.bin', help='Output file name')
    parser.add_argument('--otype', action='store', type=str, default='bin', help='Output file type (used in SAVE_BY_DIR mode)')
    parser.add_argument('--logfile', action='store', type=str, default='gentset.log', help='Output file name')
    parser.add_argument('-p', '--preproc', action='store_true', default=False, help='preprocess raw data')
    parser.add_argument('-a', '--agg', action='store_true', default=False, help='Aggregate preprocessed raw data')
    parser.add_argument('--raw_sample_rate', type=float, action='store', default=2e6, help='Raw data sample rate')
    parser.add_argument('--over_sample', type=int, action='store', default=4, help='Over sample rate')
    parser.add_argument('--preamble_time', type=float, action='store', default=8e-6, help='Preamble time (duration)')
    parser.add_argument('--class_sample_thresh', type=int, action='store', default=0, help='Minimum number of sample instances to be included in preprocessed dataset.')
    parser.add_argument('--real_im', action='store_true', default=False, help='Convert data to real and imaginary instead of magnitude and phase.')

    cargs = parser.parse_args()

    with open(cargs.logfile, 'w') as lfp:
        if cargs.save_by_dir:
            sbd = cargs.oname
            dirwalk(cargs.dirname, lfp, cargs)        
        else:
            dataset, icao_lm, preproced = dirwalk(cargs.dirname, lfp, cargs)
            if dataset is not None and cargs.write:
                writedata(cargs, cargs.oname, lfp, dataset, icao_lm, preproced=preproced)

        print(f"Completed OK!", file=lfp, flush=True)
        
    print(f"Completed OK.", flush=True)
    
    exit(0)
    
