"""
Audit the training and test data to:
1. Get the exact Benign:Attack ratio -> confirms the right pos_weight
2. Check that sequence labels actually contain attacks (not all benign)
3. Verify the test set also has attacks
"""
import glob
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, ".")

TRAIN_DIR = "processed_dataset"
TEST_DIR  = "processed_dataset/Golden_Test_Set"

def audit_dir(label, directory):
    files = glob.glob(f"{directory}/**/*_flows.parquet", recursive=True)
    # Exclude Golden_Test_Set from training count
    files = [f for f in files if "Golden_Test_Set" not in f]
    
    total, benign, attack = 0, 0, 0
    attack_types = {}
    for f in files[:50]:  # Sample 50 files for speed
        try:
            df = pd.read_parquet(f, columns=['label'])
            c = df['label'].value_counts()
            benign += c.get('Benign', 0)
            atk = c[c.index != 'Benign'].sum()
            attack += atk
            total += len(df)
            for k, v in c[c.index != 'Benign'].items():
                attack_types[k] = attack_types.get(k, 0) + v
        except:
            pass

    ratio = benign / attack if attack > 0 else float('inf')
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    print(f"  Files sampled : {len(files[:50])}")
    print(f"  Total samples : {total:,}")
    print(f"  Benign        : {benign:,} ({benign/total*100:.1f}%)")
    print(f"  Attack        : {attack:,} ({attack/total*100:.1f}%)")
    print(f"  Ratio B:A     : {ratio:.1f}:1  -> recommended pos_weight = {ratio:.0f}")
    print(f"\n  Attack types:")
    for k, v in sorted(attack_types.items(), key=lambda x: -x[1]):
        print(f"    {k:30s} : {v:,}")
    return ratio

ratio = audit_dir("TRAINING DATA (17M)", TRAIN_DIR)

files = glob.glob(f"{TEST_DIR}/**/*_flows.parquet", recursive=True)
total, benign, attack = 0, 0, 0
for f in files[:50]:
    try:
        df = pd.read_parquet(f, columns=['label'])
        c = df['label'].value_counts()
        benign += c.get('Benign', 0)
        attack += c[c.index != 'Benign'].sum()
        total += len(df)
    except:
        pass

print(f"\n{'='*55}")
print(f"  TEST DATA (Golden Test Set 6.8M)")
print(f"{'='*55}")
print(f"  Total samples : {total:,}")
print(f"  Benign        : {benign:,} ({benign/total*100:.1f}%)")
print(f"  Attack        : {attack:,} ({attack/total*100:.1f}%)")
print(f"  Ratio B:A     : {benign/attack:.1f}:1")

print(f"\n{'='*55}")
print(f"  VERDICT")
print(f"{'='*55}")
actual_ratio = benign/attack if attack > 0 else 0
current_weight = 18.0
if abs(current_ratio - 18.0) < 5 if (current_ratio := actual_ratio) else False:
    print(f"  [OK] pos_weight=18 is CORRECT for ratio {actual_ratio:.1f}:1")
else:
    print(f"  [FIX] pos_weight should be ~{actual_ratio:.0f} (current=18)")
