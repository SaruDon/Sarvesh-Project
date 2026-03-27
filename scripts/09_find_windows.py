import pandas as pd
import glob
import os
from datetime import datetime, timezone

files = glob.glob('c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/extracted_features/Friday-23-02-2018/*.csv')
output = []
for f in files:
    try:
        df = pd.read_csv(f, usecols=['frame.time_epoch'])
        if not df.empty:
            min_t = df['frame.time_epoch'].min()
            max_t = df['frame.time_epoch'].max()
            start_dt = datetime.fromtimestamp(min_t, timezone.utc)
            end_dt = datetime.fromtimestamp(max_t, timezone.utc)
            h_start = start_dt.hour
            h_end = end_dt.hour
            # PCAPs spanning the target UTC hours (14-16, 17-19, 19-21)
            filename = os.path.basename(f).replace('.csv', '')
            output.append((filename, start_dt, end_dt))
    except Exception:
        pass

output.sort(key=lambda x: x[1])
for filename, start_dt, end_dt in output:
    print(f'{filename}: {start_dt.strftime("%H:%M")} to {end_dt.strftime("%H:%M")}')
