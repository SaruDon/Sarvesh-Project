import pandas as pd
import glob
import os

day = "Wednesday-14-02-2018"
path = f"c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/extracted_features/{day}/*.csv"
files = glob.glob(path)

print(f"Scanning {len(files)} CSV files for 172.31.69 subnet...")
found_ip = False

for f in files:
    try:
        # Check first 500 rows for speed
        df = pd.read_csv(f, nrows=500)
        if 'ip.dst' in df.columns:
            matches = df[df['ip.dst'].astype(str).str.contains('172.31.69.')]
            if not matches.empty:
                print(f"FOUND TARGET SUBNET in {os.path.basename(f)}:")
                print(matches['ip.dst'].unique())
                found_ip = True
                break
    except:
        continue

if not found_ip:
    print("Subnet 172.31.69.x NOT FOUND in any sample rows.")
