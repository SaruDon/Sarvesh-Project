import pandas as pd
import glob
import os

files = glob.glob('extracted_features/Wednesday-14-02-2018/UCAP*.csv')
print(f"Auditing {len(files)} UCAP CSVs...")

for f in files:
    try:
        df = pd.read_csv(f)
        if 'frame.time_epoch' in df.columns:
            ts_min = df['frame.time_epoch'].min()
            ts_max = df['frame.time_epoch'].max()
            dt_min = pd.to_datetime(ts_min, unit='s')
            dt_max = pd.to_datetime(ts_max, unit='s')
            print(f"{os.path.basename(f)}: {dt_min} to {dt_max} ({len(df)} rows)")
    except Exception as e:
        print(f"Error reading {f}: {e}")
