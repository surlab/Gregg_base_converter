# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 14:37:11 2026

@author: SOFIE
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 14:45:14 2025

@author: sofieahrlund-richter
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  3 14:04:08 2025

@author: sofieahrlund-richter
"""

#### preprocessing data to align imaging data with wheel, visStim and pupil diameter.
### Lable with session info; animalID, depth, pradigm and puff.
### Upsample imaging frequency x2 (20Hz) to fit beahvioural data. 
### make one plot of all variable in time (?)


### prepare workspace for next
##clear all
%reset -f

# import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import glob
import os
from pathlib import Path
import re
import glob
import os

# ---- ROOTS (set these once; no need to change per session) ----
PUPIL_ROOT   = r"G:\tricolor\PilotExp2025\pupil"
VISSTIM_ROOT = r"C:\Users\SOFIE\MIT Dropbox\Sofie Richter\vipLC\scripts\jenks_visstim\SOFIE STIMEVENTS\tricolor_projections"

# You can add tokens you use as "condition" tags here
CONDITION_TOKENS = {"sal", "cno", "veh", "ctrl", "control", "drug", "na", "none"}

_DATE8_RE = re.compile(r"^20\d{6}$")       # 20250805
_DATE7_BAD_RE = re.compile(r"^22\d{5}$")   # 2250804  -> 20250804
_DEPTH_RE = re.compile(r"^\d+um$", re.IGNORECASE)

def _normalize_date_token(tok: str) -> str:
    """
    Fix common mislabel:
      225XXXX  -> 2025XXXX
      226XXXX  -> 2026XXXX
    Pattern: 7-digit '22Ydddd' -> '202Ydddd'
    """
    tok = tok.strip()
    if _DATE8_RE.match(tok):
        return tok
    if _DATE7_BAD_RE.match(tok):
        return "202" + tok[2] + tok[3:]
    return tok

def _pick_paradigm_token(tokens):
    # prefer token containing 'grating'
    for t in tokens:
        if "grating" in t.lower():
            return t
    # otherwise first non-condition token
    for t in tokens:
        if t.lower() not in CONDITION_TOKENS:
            return t
    return tokens[0] if tokens else ""

def _unique_keep_order(seq):
    out = []
    for s in seq:
        if s and s not in out:
            out.append(s)
    return out

def _first_existing_dir(candidates):
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None

def parse_ids_from_imagepath(imagepath: str):
    """
    imagepath should point to the session run folder, e.g.
    ...\\exp104.a1\\20260211\\exp104.a1.20260211.gratings-018\\

    Handles:
      - bad date tokens like 2250804 -> 20250804
      - depth token order like 0um.2025... vs 2025...0um
      - extra condition tokens at end like .sal, .cno
    """
    p = Path(str(imagepath).rstrip("/\\"))
    run_folder = p.name                                # includes -017, etc
    base_folder = re.sub(r"-\d{3}$", "", run_folder)    # remove run suffix

    parts = base_folder.split(".")
    if len(parts) < 3:
        raise ValueError(f"Unexpected run folder format: '{run_folder}'")

    animal_id = ".".join(parts[:2])
    rest = parts[2:]  # date/depth/paradigm/condition tokens live here

    # find date token anywhere in rest
    date_raw = None
    date_idx = None
    for i, tok in enumerate(rest):
        if _DATE8_RE.match(tok) or _DATE7_BAD_RE.match(tok):
            date_raw, date_idx = tok, i
            break
    if date_raw is None:
        raise ValueError(f"Could not find date token in run folder: '{run_folder}'")
    date8 = _normalize_date_token(date_raw)

    # find depth token anywhere (optional)
    depth = None
    depth_idx = None
    for i, tok in enumerate(rest):
        if _DEPTH_RE.match(tok):
            depth, depth_idx = tok, i
            break

    # other tokens (paradigm + optional condition etc.)
    other = []
    for i, tok in enumerate(rest):
        if i == date_idx:
            continue
        if depth_idx is not None and i == depth_idx:
            continue
        other.append(tok)

    # canonical session_id we will use for metadata + saving
    # (animal.date.[depth].other...)
    canon_parts = [animal_id, date8] + ([depth] if depth else []) + other
    session_id = ".".join(canon_parts)

    return run_folder, session_id, animal_id


def build_paths_from_imagepath(imagepath: str):
    imagepath = str(Path(str(imagepath).rstrip("/\\")))  # normalize
    run_folder, session_id, animal_id = parse_ids_from_imagepath(imagepath)

    # Imaging-related files
    xml_path = str(Path(imagepath) / f"{run_folder}.xml")

    # Voltage CSV: allow small variations by globbing
    voltage_glob = str(Path(imagepath) / f"{run_folder}_Cycle*_VoltageRecording_*.csv")
    voltage_matches = sorted(glob.glob(voltage_glob))
    if not voltage_matches:
        raise FileNotFoundError(f"No voltage CSV found with pattern:\n{voltage_glob}")
    voltage_path = voltage_matches[0]

    # ---- Build candidate session folder names for other roots ----
    # We need to handle:
    #   - depth before/after date
    #   - condition present or absent
    #   - raw bad-date forms (225xxxx) might exist in other roots too
    base_folder = re.sub(r"-\d{3}$", "", run_folder)
    base_parts = base_folder.split(".")
    rest = base_parts[2:]

    # extract normalized date + depth + other tokens again (same logic)
    # (kept here so build_paths can generate additional variants)
    # find date
    date_raw = None
    for tok in rest:
        if _DATE8_RE.match(tok) or _DATE7_BAD_RE.match(tok):
            date_raw = tok
            break
    date8 = _normalize_date_token(date_raw) if date_raw else None

    # find depth
    depth = None
    for tok in rest:
        if _DEPTH_RE.match(tok):
            depth = tok
            break

    # other tokens = rest excluding date/depth
    other = []
    for tok in rest:
        if tok == date_raw:
            continue
        if depth is not None and tok.lower() == depth.lower():
            continue
        other.append(tok)

    # split trailing condition if present
    cond = None
    other_no_cond = other[:]
    if other_no_cond and other_no_cond[-1].lower() in CONDITION_TOKENS:
        cond = other_no_cond[-1]
        other_no_cond = other_no_cond[:-1]

    paradigm = _pick_paradigm_token(other_no_cond if other_no_cond else other)

    # candidate session ids to try
    # canonical (animal.date.depth.other...), variants, and raw base folder
    cand = []

    if date8:
        # animal.date.depth.paradigm.[cond]
        cand.append(".".join([animal_id, date8] + ([depth] if depth else []) + other_no_cond))
        if cond:
            cand.append(".".join([animal_id, date8] + ([depth] if depth else []) + other_no_cond + [cond]))

        # animal.date.paradigm.[cond] (no depth)
        cand.append(".".join([animal_id, date8] + other_no_cond))
        if cond:
            cand.append(".".join([animal_id, date8] + other_no_cond + [cond]))

        # animal.depth.date.paradigm.[cond] (depth first)
        if depth:
            cand.append(".".join([animal_id, depth, date8] + other_no_cond))
            if cond:
                cand.append(".".join([animal_id, depth, date8] + other_no_cond + [cond]))

    # include the canonical session_id we returned (safe)
    cand.append(session_id)

    # include raw base folder as-is (may contain 225xxxx or different ordering)
    cand.append(base_folder)

    cand = _unique_keep_order([c for c in cand if c and c != animal_id])

    # ---- VISSTIM directory: try candidates, then fallback glob ----
    vis_parent = Path(VISSTIM_ROOT) / f"{animal_id}.npy"
    vis_dir_candidates = [str(vis_parent / c) for c in cand]
    visstim_dir = _first_existing_dir(vis_dir_candidates)

    if visstim_dir is None:
        if date8 is None:
            raise FileNotFoundError(f"Could not infer date from run folder '{run_folder}' for visstim search.")
        # fallback: any folder containing the normalized date, prefer ones containing paradigm
        pattern = str(vis_parent / f"*{date8}*")
        matches = [d for d in glob.glob(pattern) if os.path.isdir(d)]
        if not matches:
            raise FileNotFoundError(
                f"Could not find visstim session dir under:\n{vis_parent}\n"
                f"Tried candidates:\n  " + "\n  ".join(vis_dir_candidates) + f"\nFallback glob:\n  {pattern}"
            )
        matches.sort(key=lambda d: (paradigm.lower() not in os.path.basename(d).lower(), len(d)))
        visstim_dir = matches[0]

    stim_file = str(Path(visstim_dir) / "stim_file.npy")
    wheel_file = str(Path(visstim_dir) / "wheel_file.npy")
    if not os.path.isfile(stim_file):
        raise FileNotFoundError(f"stim_file.npy not found in: {visstim_dir}")
    if not os.path.isfile(wheel_file):
        raise FileNotFoundError(f"wheel_file.npy not found in: {visstim_dir}")

    # ---- PUPIL directory + DLC file ----
    pupil_parent = Path(PUPIL_ROOT) / animal_id
    pupil_dir_candidates = [str(pupil_parent / c) for c in cand]
    pupil_dir = _first_existing_dir(pupil_dir_candidates)

    if pupil_dir is None:
        if date8 is None:
            raise FileNotFoundError(f"Could not infer date from run folder '{run_folder}' for pupil search.")
        pattern = str(pupil_parent / f"*{date8}*")
        matches = [d for d in glob.glob(pattern) if os.path.isdir(d)]
        if not matches:
            raise FileNotFoundError(
                f"Could not find pupil session dir under:\n{pupil_parent}\n"
                f"Tried candidates:\n  " + "\n  ".join(pupil_dir_candidates) + f"\nFallback glob:\n  {pattern}"
            )
        matches.sort(key=lambda d: (paradigm.lower() not in os.path.basename(d).lower(), len(d)))
        pupil_dir = matches[0]

    # DLC file pattern can vary
    pupil_candidates = glob.glob(str(Path(pupil_dir) / f"{animal_id}*DLC*.csv"))
    if not pupil_candidates:
        pupil_candidates = glob.glob(str(Path(pupil_dir) / "*DLC*.csv"))
    if not pupil_candidates:
        raise FileNotFoundError(f"No pupil DLC CSV found in:\n{pupil_dir}")

    pupil_csv = max(pupil_candidates, key=os.path.getmtime)

    return {
        "imagepath": imagepath,
        "run_folder": run_folder,
        "session_id": session_id,   # canonical (date normalized + depth after date)
        "animal_id": animal_id,
        "xml_path": xml_path,
        "voltage_path": voltage_path,
        "visstim_dir": visstim_dir,
        "stim_file": stim_file,
        "wheel_file": wheel_file,
        "pupil_dir": pupil_dir,
        "pupil_csv": pupil_csv,
        # optional debug:
        "session_candidates": cand,
        "paradigm_token": paradigm,
        "date8": date8,
        "depth": depth,
        "condition": cond,
    }



imagepath = r"\\surflex2\2P3_data\USERBRU-S93G2VI\E\Sofie\exp104.a1\20260211\exp104.a1.20260211.gratings-018/"
paths = build_paths_from_imagepath(imagepath)

print(paths["animal_id"], paths["session_id"], paths["run_folder"])



sess = paths["session_id"].lower()


    
############################# import voltage data and find the first 5V input (start of paradigm)
### cut the trace at that point, and align with all other VisStim inputs

#voltage = pd.read_csv(imagepath +'exp104.a1.20260211.gratings-018_Cycle00001_VoltageRecording_001.csv')
voltage = pd.read_csv(paths["voltage_path"])





################# find MATLAB start 
## import direction and contrast
visstim = np.load(paths["stim_file"])## rearange to get in order
visstim = pd.DataFrame(visstim.reshape(-1, visstim.shape[-1]))

# --- compute MATLAB-start offset in the voltage/imaging clock ---
v = voltage[' Input 1'].to_numpy(float)
t_ms = voltage['Time(ms)'].to_numpy(float)

thr = 4.9
rise_idx = np.where((v[:-1] < thr) & (v[1:] >= thr))[0] + 1
tV0 = t_ms[rise_idx[0]] / 1000.0              # sec, first true stimulus onset in voltage clock

tM0 = float(visstim.iloc[0, 3])               # sec, first stim onset in MATLAB session clock

t_matlab0_in_voltage_s = tV0 - tM0             # sec, where MATLAB start sits in voltage clock

    



#### interapolate to 20Hz
## make voltage recording time adjusted to the rest of the starting points (wheel etc)
voltage['Time(ms)'] = voltage['Time(ms)'] - (t_matlab0_in_voltage_s * 1000.0)
## make timestamps daytime format
voltage['datetime'] = pd.to_datetime(voltage['Time(ms)'], unit='ms')
# new range that we want to sample data
new_range = pd.date_range(voltage.datetime[0], voltage.datetime.values[-1], freq='50ms')
## set datetime as the index
voltage = voltage.set_index('datetime')
### fuse the two indexes in time and interpolate voltage values inbetween, then reindex based on new sampleing rate, then reset index
voltage = voltage.reindex(voltage.index.union(new_range)).interpolate(method='time').reindex(new_range).reset_index()



################################################################ import arrays
## specific files
F= 'interleaved\suite2p\plane0\F.npy'
Fneu= 'interleaved\suite2p\plane0\Fneu.npy'
roi= 'interleaved\suite2p\plane0\iscell.npy'

################################################################ import arrays
trace = np.load(imagepath+F)
neuropil = np.load(imagepath+Fneu)
iscell = np.load(imagepath+roi)



 ## subtract 0.8 of neuropil
trace= np.subtract(trace, (neuropil*0.8))





################################################### import classification
classification = np.load(imagepath+ 'interleaved/cellpose/classification.npy', allow_pickle=True)

classification_dict = classification.item()   # extract the dict

#### turn classification to readable array
cls = classification_dict
keys = ['mCherry', 'mNeptune', 'tdTomato']

# Stack the boolean arrays column-wise → shape (N_rois, 3)
bool_matrix = np.column_stack([cls[k] for k in keys])

# Where is there any True?
has_any = bool_matrix.any(axis=1)

# Prepare result array of strings
labels = np.full(bool_matrix.shape[0], 'unclassified', dtype=object)

# For rows that have at least one True, pick the first True column
labels[has_any] = np.array(keys)[bool_matrix[has_any].argmax(axis=1)]

print(labels[:20])   # this is your one row/list/column of strings

###########add classification info
M = trace.shape[0]
N = labels.shape[0]

# Create a full-length column filled with 'unlabled'
padded_labels = np.full(M, 'unlabled', dtype=object)

# Bottom-align: put your labels in the last N rows
padded_labels[M-N:] = labels

### att to F
labled_trace = np.column_stack([trace, padded_labels])




######## add iscell info
labled_trace = np.concatenate((labled_trace, iscell), axis=1)

# 1) keep only ROIs where second-to-last column != 0
labled_trace = labled_trace[labled_trace[:,-2] != 0]

# 2) drop the last two columns
labled_trace = labled_trace[:,:-2]

# 3) make into a DataFrame (with ROIs now as columns after transpose)
labled_trace = pd.DataFrame(labled_trace.T)




## make cell type part of the column name for each cell 
# Take the last row
last_row =labled_trace.iloc[-1]

# Build new column names as "number_string"
labled_trace.columns = [f"{col}_{str(val)}" for col, val in zip(labled_trace.columns, last_row)]

print(labled_trace)

#### remove last row
labled_trace=labled_trace.iloc[:-1]

### apply rolling window smooting
labled_trace= labled_trace.rolling(window=3, win_type='gaussian', center=True).mean(std=1)







############################################################ import timestamps
#tree = ET.parse(imagepath+'exp104.a1.20260211.gratings-018.xml')
tree = ET.parse(paths["xml_path"])

root = tree.getroot() 
# create timestamp list
timestamps= []

# loop over xml file to get a list of all timestamps
for i in root.iter('Frame'):
    #print('relativeTime', "=", i.attrib['relativeTime'])
    timestamps.append(i.attrib['relativeTime'])   
    
## add tiestamps to trace (make numeric) and add delay (to align with rest of data)
labled_trace['timestamp'] = pd.Series(timestamps).apply(pd.to_numeric, errors='coerce')
labled_trace['timestamp'] = labled_trace['timestamp'] - t_matlab0_in_voltage_s
## drop last two rows with NA values as this is ROI stats
labled_trace.dropna(subset=["timestamp"], axis=0, inplace=True)  

del tree, root, timestamps, i


######################################################### interapolate to 20Hz

## make timestamps daytime format
labled_trace['datetime'] = pd.to_datetime(labled_trace['timestamp'], unit='s')
# new range that we want to sample data
new_range = pd.date_range(labled_trace.datetime[0], labled_trace.datetime.values[-1], freq='50ms')
## set datetime as the index
labled_trace = labled_trace.set_index('datetime')
### fuse the two indexes in time and interpolate imaging values inbetween, then reindex based on new sampleing rate, then reset index
trace20Hz = labled_trace.reindex(labled_trace.index.union(new_range)).interpolate(method='time').reindex(new_range).reset_index()

del trace, new_range



############################################################## extract VisStim info
## import direction and contrast
visstim = np.load(paths["stim_file"])


#visstim = np.load(r'C:\Users\SOFIE\MIT Dropbox\Sofie Richter\vipLC\scripts\jenks_visstim\SOFIE STIMEVENTS\tricolor_projections\exp104.a1.npy\exp104.a1.20260211.gratings/stim_file.npy')
## rearange to get in order
visstim = pd.DataFrame(visstim.reshape(-1, visstim.shape[-1]))


####### loop visstim info and add it to the voltage input
voltage['direction'] = 'nan'
voltage['contrast']  = 0
idx = 0
n_trials = len(visstim)

for t in range(voltage.shape[0]-1):

    # STOP once we have assigned all trials
    if idx >= n_trials:
        break

    if voltage.loc[t, ' Input 1'] > 4.9 and voltage.loc[t+1, ' Input 1'] > 4.9:
        voltage.loc[t, 'direction'] = visstim.iloc[idx, 0]
        voltage.loc[t, 'contrast']  = visstim.iloc[idx, 2]

    elif voltage.loc[t, ' Input 1'] > 4.9 and voltage.loc[t+1, ' Input 1'] < 4.9:
        voltage.loc[t, 'direction'] = visstim.iloc[idx, 0]
        voltage.loc[t, 'contrast']  = visstim.iloc[idx, 2]
        idx += 1

    else:
        voltage.loc[t, 'direction'] = 'nan'
        voltage.loc[t, 'contrast']  = 0

print("Assigned trials:", idx, "out of", n_trials)

        
#del visstim, idx, t, newrow

################################################################## add wheel info

## import wheel data
#wheel = pd.DataFrame(np.load(r'C:\Users\SOFIE\MIT Dropbox\Sofie Richter\vipLC\scripts\jenks_visstim\SOFIE STIMEVENTS\tricolor_projections\exp104.a1.npy\exp104.a1.20260211.gratings/wheel_file.npy'))
wheel = pd.DataFrame(np.load(paths["wheel_file"]))
## make wheel data cm/sec
#wheel[1]=wheel[1]/130
## new kyle value
wheel[1]=abs(wheel[1]*0.316)

### apply Gaussian smooting on the raw wheel trace 
wheel[1] = wheel[1].rolling(window=5, win_type='gaussian', center=True).mean(std=1)

## remove jitter, values below 0.1cm/s
#wheel.loc[wheel[1]<=0.1, [1]  ] = 0


## make timestamps daytime format
wheel['index'] = pd.to_datetime(wheel[0], unit='s')

## fuse to closest voltage time-value and name column 'speed_cm/s'
voltage = pd.merge_asof(voltage, wheel[['index', 1]], direction='nearest').fillna(wheel.quantile(0.50))
voltage = voltage.rename(columns={1: 'speed_cm/s'})

### if wheel was broken 
#voltage["speed_cm/s"] = 0.0 if wheel.empty else wheel.iloc[:len(voltage), 0].to_numpy()


########################################################################## add pupil data
    

#pupil = pd.read_csv(r'G:\tricolor\PilotExp2025\pupil\to run\exp104.a1\exp104.a1.20260211.gratings/exp104.a1.20260211.gratings_20-cStackDLC_resnet50_Tricolor_pilot_February2026Feb18shuffle1_50000.csv')
pupil = pd.read_csv(paths["pupil_csv"])

#tstamp = pd.read_table(folder2+animalid+'.pupils/'+sess+'/'+sess+'_tStamp.txt')


### reset column names 
pupil.columns = (pupil.iloc[0] + '_' + pupil.iloc[1])
pupil = pupil.iloc[2:].reset_index(drop=True)

### make numbers float
pupil=pupil.astype(float)

### calculate average diameter in pixels
## vertical diameter
pupil['verticalD']= np.sqrt((pupil.vright_x - pupil.vdown_x) ** 2 + 
                                (pupil.vright_y - pupil.vdown_y)** 2)
## horizontal diameter
pupil['horizontalD']= np.sqrt((pupil.hleft_x - pupil.hright_x) ** 2 + 
                                (pupil.hleft_y - pupil.hright_y)** 2)                                 
## diagonal 1 o'clock diameter
pupil['Clock1D']= np.sqrt((pupil.c1_x - pupil.c8_x) ** 2 + 
                                (pupil.c1_y - pupil.c8_y)** 2)
## diagonal 4 o'clock diameter
pupil['Clock4D']= np.sqrt((pupil.c4_x - pupil.c11_x) ** 2 + 
                                (pupil.c4_y - pupil.c11_y)** 2)
#### mean diameter
pupil['diameter(pix)']= pupil.loc[:, ['verticalD','horizontalD','Clock1D', 'Clock4D' ]].mean(axis=1)

## remove outliers from DLC and replace them with median
pupil['diameter(pix)'] = np.where(pupil['diameter(pix)'] > pupil['diameter(pix)'].quantile(0.95), pupil['diameter(pix)'].quantile(0.50), pupil['diameter(pix)'])

pupil['diameter(pix)'] = np.where(pupil['diameter(pix)'] < pupil['diameter(pix)'].quantile(0.01), pupil['diameter(pix)'].quantile(0.50), pupil['diameter(pix)'])

 ##################################################################################################################
    
### apply Gaussian smooting on the raw wheel trace 
pupil['diameter(pix)'] = pupil['diameter(pix)'].rolling(window=5, win_type='gaussian', center=True).mean(std=1)


# Compute zscore for pupil diameter
col_mean = pupil['diameter(pix)'].mean()
col_std = pupil['diameter(pix)'].std()
pupil["pupil_zscore"] = (pupil['diameter(pix)'] - col_mean)/col_std







## create new 'fake' timestamps - one from data are wrong
end = len(pupil)
tstamp = list(range(end + 1))
tstamp = [a/20 for a in tstamp]

## fuse t stamps with pupil diameter, face and z-score
pupilT = pd.concat([pd.DataFrame(tstamp), pupil.loc[:,['pupil_zscore', 'diameter(pix)']]], axis=1 )


## make timestamps daytime format
pupilT['index'] = pd.to_datetime(pupilT[0], unit='s')

## fuse diameter and z-score to closest voltage time-value, fill missing values with median 
voltage = pd.merge_asof(voltage, pupilT[['index', 'pupil_zscore', 'diameter(pix)']], direction='nearest').fillna(pupilT.quantile(0.50))

### make Time(ms) into secons (new column)
voltage['time(s)'] = voltage['Time(ms)']/1000

#del pupil, pupilT, col_mean, col_std, tstamp




############# sanity checks 

# -------------------------
# 0) define tM0 (MATLAB time of first stim)
# -------------------------
tM0 = float(visstim.iloc[0, 3])  # seconds, MATLAB session clock
print("tM0 (MATLAB stim1 onset, s):", tM0)

# -------------------------
# 1) detect voltage pulse onsets robustly (avoid 2.5 V artifacts)
# -------------------------
v = voltage[' Input 1'].to_numpy(float)
t_ms = voltage['Time(ms)'].to_numpy(float)

thr = 4.9
rise_idx = np.where((v[:-1] < thr) & (v[1:] >= thr))[0] + 1
voltage_onsets_volt_s = t_ms[rise_idx] / 1000.0  # seconds, voltage/imaging clock

print("Voltage rises found (thr=4.9V):", len(voltage_onsets_volt_s))
print("First voltage rise time (voltage clock, s):", voltage_onsets_volt_s[0])

# also show the old (>=5) sample-based estimate for comparison (should be close)
delay_ms_ge5 = float(voltage.loc[(voltage[' Input 1'] >= 5.0).idxmax(), 'Time(ms)'])
print("First sample >=5V time (ms):", delay_ms_ge5, " -> s:", delay_ms_ge5/1000.0)

# -------------------------
# 2) compute MATLAB-start offset in the voltage clock
#    MATLAB start in voltage clock = tV0 - tM0
# -------------------------
tV0 = float(voltage_onsets_volt_s[0])             # first true pulse onset in voltage clock
t_matlab0_in_voltage_s = tV0 - tM0                # seconds

print("tV0 (voltage stim1 onset, s):", tV0)
print("t_matlab0_in_voltage_s (s):", t_matlab0_in_voltage_s)
print("Check: stim1 in MATLAB time from voltage should be:", (tV0 - t_matlab0_in_voltage_s), "(should equal tM0)")

# -------------------------
# 3) convert ALL voltage onsets into MATLAB timebase
# -------------------------
voltage_onsets_matlab_s = voltage_onsets_volt_s - t_matlab0_in_voltage_s

print("First voltage onset in MATLAB timebase (s):", voltage_onsets_matlab_s[0], "(should equal tM0)")

# -------------------------
# 4) read visstim onset list (MATLAB timebase) and compare
# -------------------------
vis_onsets_s = pd.to_numeric(visstim.iloc[:, 3], errors="coerce").dropna().to_numpy(float)
print("Visstim onsets found:", len(vis_onsets_s))

n = min(len(voltage_onsets_matlab_s), len(vis_onsets_s))
diff_ms = (voltage_onsets_matlab_s[:n] - vis_onsets_s[:n]) * 1000.0

print("\n--- Timing agreement (index-matched) ---")
print("n compared:", n)
print("mean diff (ms):", np.nanmean(diff_ms))
print("median diff (ms):", np.nanmedian(diff_ms))
print("std diff (ms):", np.nanstd(diff_ms))
print("max |diff| (ms):", np.nanmax(np.abs(diff_ms)))

tol_ms = 50
bad = np.where(np.abs(diff_ms) > tol_ms)[0]
print(f"Trials with |diff| > {tol_ms} ms:", len(bad))
if len(bad) > 0:
    for k in bad[:10]:
        print(f"trial {k+1}: voltage={voltage_onsets_matlab_s[k]:.4f}s, "
              f"visstim={vis_onsets_s[k]:.4f}s, diff={diff_ms[k]:.1f}ms")

# -------------------------
# 5) optional: check ISI consistency in both streams
# -------------------------
if len(voltage_onsets_matlab_s) > 1:
    dv = np.diff(voltage_onsets_matlab_s)
    print("\nVoltage ISI: median", np.median(dv), "s | min", dv.min(), "s | max", dv.max(), "s")

if len(vis_onsets_s) > 1:
    ds = np.diff(vis_onsets_s)
    print("Visstim ISI: median", np.median(ds), "s | min", ds.min(), "s | max", ds.max(), "s")







    
    
################################################### final step, fuse behavioural data with imaging data and save it

## fuse diameter and z-score to closest voltage time-value 
exp = pd.merge_asof(trace20Hz, voltage[['index', 'time(s)', ' Input 1', 'direction', 'contrast',  'speed_cm/s', 'pupil_zscore', 'diameter(pix)']], direction='nearest')



# drop negative time values so you can start from 0
exp.drop(exp[exp['time(s)'] < 0].index, inplace=True)
exp= exp.reset_index(drop=True)



from pathlib import Path
import os

# ---- optional: set once near the top ----
SURFLEX_OUT_ROOT = r"\\surflex2\2P3_data\Sofie\data"
DROPBOX_OUT_ROOT = r"C:\Users\SOFIE\MIT Dropbox\Sofie Richter\Tricolor_Pilot2025"

animal_id  = paths["animal_id"]   # e.g. exp104.a1
session_id = paths["session_id"]  # e.g. exp104.a1.20260211.gratings  (no -018)

# add session metadata
exp["animal"] = animal_id
exp["session"] = session_id
exp["condition"] = paths["condition"]   # keep as-is, or make it a variable at top

# drop negative time values so you can start from 0 (MATLAB start)
exp = exp.loc[exp["time(s)"] >= 0].reset_index(drop=True)

# build output paths
csv_name = f"{session_id}.csv"
pdf_name = f"{session_id}.pdf"

surflex_csv = str(Path(SURFLEX_OUT_ROOT) / csv_name)
dropbox_csv = str(Path(DROPBOX_OUT_ROOT) / csv_name)
surflex_pdf = str(Path(SURFLEX_OUT_ROOT) / pdf_name)

# ensure output dirs exist
os.makedirs(SURFLEX_OUT_ROOT, exist_ok=True)
os.makedirs(DROPBOX_OUT_ROOT, exist_ok=True)

# save
exp.to_csv(surflex_csv, index=False)
exp.to_csv(dropbox_csv, index=False)

# plot overview and save pdf
ax = exp.iloc[:, -18:-2].plot(subplots=True, figsize=(8.27, 11.7))
plt.suptitle(session_id)  # or sess if you prefer
plt.tight_layout()
plt.savefig(surflex_pdf, dpi=300, orientation="portrait")
#plt.close("all")

print("Saved:")
print("  ", surflex_csv)
print("  ", dropbox_csv)
print("  ", surflex_pdf)























 

    
    
    
    
    
    