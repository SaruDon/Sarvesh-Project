import pandas as pd
import glob
import os

day = "Wednesday-14-02-2018"
path = f"c:/Users/Student/.gemini/antigravity/scratch/sarvesh-project/processed_dataset/{day}/*_flows.parquet"
files = glob.glob(path)

print(f"Checking labels in {len(files)} parquet files for {day}...")

found_attacks = False
for f in files:
    try:
        df = pd.read_parquet(f)
        counts = df['label'].value_counts()
        if len(counts) > 1 or 'Benign' not in counts:
            print(f"{os.path.basename(f)} labels:")
            print(counts)
            found_attacks = True
    except Exception as e:
        print(f"Error reading {f}: {e}")

if not found_attacks:
    print("No attack labels found yet.")
