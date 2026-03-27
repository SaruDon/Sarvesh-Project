import pandas as pd
import glob
import os

day = "Wednesday-14-02-2018"
path = f"c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/processed_dataset/{day}/*_flows.parquet"
files = glob.glob(path)

print(f"Checking {len(files)} files for {day}...")
found_attack = False

for f in files:
    df = pd.read_parquet(f)
    if 'label' in df.columns:
        counts = df['label'].value_counts()
        if len(counts) > 1 or (len(counts) == 1 and counts.index[0] != 'Benign'):
            print(f"FOUND ATTACKS in {os.path.basename(f)}:")
            print(counts)
            found_attack = True
    elif 'label_<lambda>' in df.columns:
        counts = df['label_<lambda>'].value_counts()
        if len(counts) > 1 or (len(counts) == 1 and counts.index[0] != 'Benign'):
            print(f"FOUND ATTACKS in {os.path.basename(f)}:")
            print(counts)
            found_attack = True

if not found_attack:
    print("No attacks found in any file.")
