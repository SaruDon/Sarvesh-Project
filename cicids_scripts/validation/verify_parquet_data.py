import pandas as pd
import numpy as np
import os
import glob
from tqdm import tqdm
from collections import Counter

def verify_data(day_dir):
    print(f"--- Verifying Data for {day_dir} ---")
    
    flow_files = glob.glob(os.path.join(day_dir, "*_flows.parquet"))
    seq_files = glob.glob(os.path.join(day_dir, "*_sequences.parquet"))
    
    if not flow_files:
        print("No flow files found!")
        return

    # Check Flows
    print(f"\n1. FLOWS CHECK (Sample: {os.path.basename(flow_files[0])})")
    df_flow = pd.read_parquet(flow_files[0])
    print(f"   Shape: {df_flow.shape}")
    
    # Identify label column (could be 'label' or 'label_<lambda>')
    label_col = [c for c in df_flow.columns if 'label' in c][0]
    print(f"   Label column identified as: {label_col}")
    
    print(f"   Labels found: {df_flow[label_col].value_counts().to_dict()}")
    print(f"   Any Nulls: {df_flow.isnull().sum().sum()}")

    # Check Sequences
    if seq_files:
        print(f"\n2. SEQUENCES CHECK (Sample: {os.path.basename(seq_files[0])})")
        df_seq = pd.read_parquet(seq_files[0])
        print(f"   Shape: {df_seq.shape}")
        if not df_seq.empty:
            first_seq = np.array(df_seq['sequence_features'].iloc[0])
            print(f"   Sequence Feature Type: {type(df_seq['sequence_features'].iloc[0])}")
            print(f"   Sequence Shape (Flattened): {first_seq.shape}")
            print(f"   Labels found: {df_seq['label'].value_counts().to_dict()}")
            
    # Daily Label Summary
    print("\n3. SEARCHING FOR ATTACK LABELS ACROSS ALL FILES...")
    attack_files = []
    labels_found = Counter()
    
    for f in tqdm(flow_files, desc="Scanning for labels"):
        temp_df = pd.read_parquet(f, columns=[label_col])
        counts = temp_df[label_col].value_counts()
        labels_found += Counter(counts.to_dict())
        if any(label != 'Benign' for label in counts.index):
            attack_files.append((os.path.basename(f), counts.to_dict()))
    
    print(f"\n   Aggregate Label distribution: {dict(labels_found)}")
    if attack_files:
        print(f"   Attack data found in {len(attack_files)} files:")
        for name, counts in attack_files[:5]:
            print(f"     - {name}: {counts}")
    else:
        print("   !!! WARNING: NO ATTACK LABELS FOUND IN ANY FILE!")

if __name__ == "__main__":
    verify_data("processed_dataset/Friday-02-03-2018")
