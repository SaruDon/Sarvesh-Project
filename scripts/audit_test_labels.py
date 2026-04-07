import pandas as pd
import glob
import collections
from tqdm import tqdm

files = glob.glob('processed_dataset/Golden_Test_Set/**/*_flows.parquet', recursive=True)
counts = collections.Counter()
print(f"Checking {len(files)} flow files in Golden_Test_Set...")
for f in tqdm(files):
    try:
        df = pd.read_parquet(f, columns=['label'])
        counts.update(df['label'].tolist())
    except Exception as e:
        print(f"Error reading {f}: {e}")

print("\n--- GLOBAL TEST SET LABEL COUNTS ---")
for label, count in counts.items():
    print(f"{label}: {count}")
