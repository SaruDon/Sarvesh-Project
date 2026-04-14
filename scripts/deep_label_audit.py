"""
Deep label audit: check the actual label distribution across
both training shards and the Golden Test Set.
Also check sequence files to verify they carry attack labels.
"""
import glob
import pandas as pd
import numpy as np

TRAIN_DIR = "processed_dataset"
TEST_DIR  = "processed_dataset/Golden_Test_Set"

def audit(name, pattern, limit=30):
    files = glob.glob(pattern, recursive=True)
    files = [f for f in files if "Golden_Test_Set" not in f][:limit]
    
    all_labels = []
    for f in files:
        try:
            df = pd.read_parquet(f, columns=['label'])
            all_labels.extend(df['label'].tolist())
        except Exception as e:
            pass
    
    if not all_labels:
        print(f"\n{name}: NO DATA FOUND")
        return
    
    s = pd.Series(all_labels).value_counts()
    total = len(all_labels)
    attack = total - s.get('Benign', 0)
    benign = s.get('Benign', 0)
    print(f"\n{'='*55}")
    print(f"  {name} ({len(files)} files, {total:,} rows)")
    print(f"{'='*55}")
    for label, cnt in s.items():
        print(f"  {label:30s} : {cnt:,} ({cnt/total*100:.1f}%)")
    print(f"  ---")
    if attack > 0:
        print(f"  Benign:Attack ratio = {benign/attack:.1f}:1")
        print(f"  -> Recommended pos_weight = {benign/attack:.0f}")
    else:
        print(f"  *** NO ATTACKS FOUND IN THESE FILES ***")

# Training flows
audit("TRAINING FLOWS", f"{TRAIN_DIR}/**/*_flows.parquet")

# Training sequences
audit("TRAINING SEQUENCES", f"{TRAIN_DIR}/**/*_sequences.parquet")

# Test flows
files = glob.glob(f"{TEST_DIR}/**/*_flows.parquet", recursive=True)[:30]
all_labels = []
for f in files:
    try:
        df = pd.read_parquet(f, columns=['label'])
        all_labels.extend(df['label'].tolist())
    except: pass
s = pd.Series(all_labels).value_counts()
total = len(all_labels)
attack = total - s.get('Benign', 0)
benign = s.get('Benign', 0)
print(f"\n{'='*55}")
print(f"  GOLDEN TEST SET ({len(files)} files, {total:,} rows)")
print(f"{'='*55}")
for label, cnt in s.items():
    print(f"  {label:30s} : {cnt:,} ({cnt/total*100:.1f}%)")
if attack > 0:
    print(f"  Benign:Attack ratio = {benign/attack:.1f}:1")
else:
    print(f"  *** NO ATTACKS in sample ***")
