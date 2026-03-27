import pandas as pd
import glob
import os

day = "Wednesday-14-02-2018"
path = f"c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/extracted_features/{day}/*.csv"
files = glob.glob(path)

print(f"Scanning {len(files)} CSV files for Port 21/22 activity...")
found_activity = False

for f in files:
    try:
        df = pd.read_csv(f)
        if 'tcp.dstport' in df.columns:
            # Check for Port 21 (FTP) and 22 (SSH)
            matches = df[df['tcp.dstport'].isin([21, 22, '21', '22'])]
            if not matches.empty:
                print(f"FOUND ACTIVITY in {os.path.basename(f)}:")
                print(matches[['ip.src', 'ip.dst', 'tcp.dstport']].drop_duplicates())
                found_activity = True
                # Don't break, see if we find 172.31.69.25
                if '172.31.69.25' in matches['ip.dst'].astype(str).values:
                    print("!!! MATCHED TARGET IP 172.31.69.25 !!!")
    except:
        continue

if not found_activity:
    print("No Port 21/22 activity found in any file.")
