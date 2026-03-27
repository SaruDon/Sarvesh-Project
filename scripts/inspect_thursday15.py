import pandas as pd
import glob
import os
from datetime import datetime, timezone

files = glob.glob('c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/extracted_features/Thursday-15-02-2018/*.csv')
print(f"Inspecting {len(files)} files...")

for f in files[:10]:
    try:
        df = pd.read_csv(f, nrows=1000)
        if 'frame.time_epoch' in df.columns:
            ts = df['frame.time_epoch'].dropna().iloc[0]
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            ips = df['ip.dst'].dropna().unique()[:5]
            print(f"{os.path.basename(f)}: Start Time (UTC): {dt.strftime('%Y-%m-%d %H:%M:%S')}, Sample IPs: {list(ips)}")
    except Exception as e:
        print(f"Error reading {f}: {e}")
