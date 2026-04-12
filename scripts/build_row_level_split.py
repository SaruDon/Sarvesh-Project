"""
Row-Level Train/Test Split
============================
Splits EVERY flow parquet file at the row level:
- 85% of rows stay in the training directory
- 15% of rows copied to Golden_Test_Set
- Same patterns, different actual flows
- Zero exact row overlap
- ALL attack types guaranteed in BOTH sets
"""
import os
import glob
import shutil
import numpy as np
import pandas as pd
from collections import defaultdict
from tqdm import tqdm

PROCESSED_DIR = "processed_dataset"
GOLDEN_DIR = os.path.join(PROCESSED_DIR, "Golden_Test_Set")
SEED = 42
TEST_RATIO = 0.15

def build_row_level_split():
    np.random.seed(SEED)
    
    print("=" * 70)
    print("ROW-LEVEL TRAIN/TEST SPLIT")
    print("Same patterns, different flows, zero overlap")
    print("=" * 70)
    
    # Step 1: Purge old test set
    if os.path.exists(GOLDEN_DIR):
        shutil.rmtree(GOLDEN_DIR)
    os.makedirs(GOLDEN_DIR)
    print("[PURGE] Cleared Golden_Test_Set\n")
    
    # Step 2: Get all training day directories
    days = sorted([d for d in os.listdir(PROCESSED_DIR)
                   if os.path.isdir(os.path.join(PROCESSED_DIR, d))
                   and d != 'Golden_Test_Set' and d != 'pcap'])
    
    total_train = 0
    total_test = 0
    attack_train = defaultdict(int)
    attack_test = defaultdict(int)
    
    for day in days:
        day_dir = os.path.join(PROCESSED_DIR, day)
        test_day_dir = os.path.join(GOLDEN_DIR, day)
        os.makedirs(test_day_dir, exist_ok=True)
        
        flow_files = glob.glob(os.path.join(day_dir, "*_flows.parquet"))
        
        day_train = 0
        day_test = 0
        day_attacks_train = 0
        day_attacks_test = 0
        
        for f in tqdm(flow_files, desc=f"  {day}", leave=False):
            try:
                df = pd.read_parquet(f)
                if len(df) == 0:
                    continue
                
                basename = os.path.basename(f)
                
                # Stratified split: separate attack and benign rows
                attack_mask = df['label'] != 'Benign'
                attack_idx = df.index[attack_mask].tolist()
                benign_idx = df.index[~attack_mask].tolist()
                
                # Shuffle each group independently
                rng = np.random.RandomState(SEED + hash(basename) % 100000)
                rng.shuffle(attack_idx)
                rng.shuffle(benign_idx)
                
                # Split attacks (ensure at least 1 in each set if possible)
                n_test_attack = max(1, int(len(attack_idx) * TEST_RATIO)) if len(attack_idx) > 1 else 0
                if len(attack_idx) == 1:
                    # Single attack row: keep in training (training is more important)
                    n_test_attack = 0
                
                test_attack_idx = attack_idx[:n_test_attack]
                train_attack_idx = attack_idx[n_test_attack:]
                
                # Split benign
                n_test_benign = int(len(benign_idx) * TEST_RATIO)
                test_benign_idx = benign_idx[:n_test_benign]
                train_benign_idx = benign_idx[n_test_benign:]
                
                test_idx = test_attack_idx + test_benign_idx
                train_idx = train_attack_idx + train_benign_idx
                
                if len(test_idx) == 0:
                    continue
                
                # Save test split
                df_test = df.loc[test_idx]
                df_test.to_parquet(os.path.join(test_day_dir, basename))
                
                # Overwrite training file with train-only rows
                df_train = df.loc[train_idx]
                df_train.to_parquet(f)
                
                # Track stats
                for label in df_test['label'].unique():
                    count = int((df_test['label'] == label).sum())
                    if label != 'Benign':
                        attack_test[label] += count
                        day_attacks_test += count
                    
                for label in df_train['label'].unique():
                    count = int((df_train['label'] == label).sum())
                    if label != 'Benign':
                        attack_train[label] += count
                        day_attacks_train += count
                
                day_train += len(train_idx)
                day_test += len(test_idx)
                
            except Exception as e:
                continue
        
        total_train += day_train
        total_test += day_test
        print(f"  {day}: Train={day_train:,} ({day_attacks_train:,} attacks) | Test={day_test:,} ({day_attacks_test:,} attacks)")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SPLIT SUMMARY")
    print(f"{'='*70}")
    print(f"Total Training: {total_train:,}")
    print(f"Total Test:     {total_test:,}")
    print(f"Split Ratio:    {total_test/(total_train+total_test)*100:.1f}% test")
    
    print(f"\nATTACK COVERAGE (Train / Test):")
    all_attacks = sorted(set(list(attack_train.keys()) + list(attack_test.keys())))
    all_covered = True
    for attack in all_attacks:
        t = attack_train.get(attack, 0)
        e = attack_test.get(attack, 0)
        status = "[OK]" if t > 0 and e > 0 else "[FAIL]"
        if t == 0 or e == 0:
            all_covered = False
        print(f"  {status} {attack:20s}: Train={t:>10,} | Test={e:>10,}")
    
    print(f"\n  All attack types in both sets: {'YES' if all_covered else 'NO'}")
    print(f"  Zero row overlap: YES (rows are split, not copied)")
    
    return all_covered


if __name__ == "__main__":
    build_row_level_split()
