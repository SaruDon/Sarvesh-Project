import pandas as pd
import glob
import os

path = "extracted_features/Thursday-15-02-2018/*.csv"
files = glob.glob(path)
target_ip = "172.31.67.22"

print(f"Checking {len(files)} files for DoS target {target_ip}...")

found_count = 0
for f in files:
    try:
        df = pd.read_csv(f)
        if ((df['ip.src'] == target_ip) | (df['ip.dst'] == target_ip)).any():
            print(f"Found traffic in {os.path.basename(f)}")
            found_count += 1
            if found_count >= 5:
                print("Found enough samples.")
                break
    except Exception as e:
        pass

if found_count == 0:
    print("No DoS traffic found in these fragments.")
else:
    print(f"Verified DoS traffic in {found_count} fragments.")
