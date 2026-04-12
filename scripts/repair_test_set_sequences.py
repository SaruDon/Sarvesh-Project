import os
import glob
import pandas as pd
import numpy as np
import shutil
from tqdm import tqdm

PROCESSED_DIR = "processed_dataset"
GOLDEN_DIR = os.path.join(PROCESSED_DIR, "Golden_Test_Set")
SEED = 42
TEST_RATIO = 0.15

def repair_sequences():
    print("Repairing Golden_Test_Set: Synchronizing Sequences...")
    
    # Get all flow files in the test set
    test_flows = glob.glob(os.path.join(GOLDEN_DIR, "**", "*_flows.parquet"), recursive=True)
    repair_count = 0
    
    for flow_path in tqdm(test_flows):
        day_dir = os.path.split(os.path.dirname(flow_path))[-1]
        basename = os.path.basename(flow_path)
        seq_basename = basename.replace("_flows.parquet", "_sequences.parquet")
        
        # Target path in Golden_Test_Set
        dest_seq_path = os.path.join(os.path.dirname(flow_path), seq_basename)
        
        if os.path.exists(dest_seq_path):
            continue # Already repaired
            
        # Source sequence file in training directory
        src_seq_path = os.path.join(PROCESSED_DIR, day_dir, seq_basename)
        
        if not os.path.exists(src_seq_path):
            # print(f"Warning: Source sequence missing for {basename}")
            continue
            
        try:
            df_test_flow = pd.read_parquet(flow_path)
            df_full_seq = pd.read_parquet(src_seq_path)
            
            # Reconstruction Logic: 
            # If lengths originally matched, we'd use the indices.
            # But they don't (Flows: 6000, Seqs: 2000).
            # The most reliable fallback is a random proportional sample
            # OR if the test set rows have indices that fit in the seq range.
            
            test_idx = df_test_flow.index.tolist()
            
            if len(df_full_seq) > max(test_idx, default=0):
                # Potential 1:1 match by index (indices are within range)
                df_test_seq = df_full_seq.loc[df_full_seq.index.intersection(test_idx)]
                if len(df_test_seq) > 0:
                    df_test_seq.to_parquet(dest_seq_path)
                    repair_count += 1
                    continue
            
            # Potential 2: Random proportional sample (as per build_test_set_v2.py)
            np.random.seed(SEED + hash(basename) % 1000)
            n_test = max(1, int(len(df_full_seq) * TEST_RATIO))
            indices = np.random.permutation(len(df_full_seq))[:n_test]
            df_test_seq = df_full_seq.iloc[indices]
            df_test_seq.to_parquet(dest_seq_path)
            repair_count += 1
            
        except Exception as e:
            print(f"Error repairing {basename}: {e}")
            
    print(f"Synchronization complete. Added {repair_count} sequence files to Golden_Test_Set.")

if __name__ == "__main__":
    repair_sequences()
