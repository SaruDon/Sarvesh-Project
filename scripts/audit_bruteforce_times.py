import pandas as pd
import glob
import os

day = "Wednesday-14-02-2018"
path = f"c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/extracted_features/{day}/*.csv"
files = glob.glob(path)

print(f"Auditing activity times for {day}...")

results = []

for f in files:
    try:
        df = pd.read_csv(f)
        if 'tcp.dstport' in df.columns:
            matches = df[df['tcp.dstport'].isin([21, 22, '21', '22'])]
            if not matches.empty:
                matches['time'] = pd.to_datetime(matches['frame.time_epoch'], unit='s')
                for _, row in matches.iterrows():
                    results.append({
                        'time': row['time'],
                        'src': row['ip.src'],
                        'dst': row['ip.dst'],
                        'port': row['tcp.dstport']
                    })
    except:
        continue

if results:
    res_df = pd.DataFrame(results)
    print("Summary of Port 21/22 Activity:")
    print(res_df.groupby(['dst', 'port']).agg({'time': ['min', 'max'], 'src': 'nunique'}))
else:
    print("No relevant activity found.")
