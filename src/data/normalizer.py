import os
import glob
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
from tqdm import tqdm

PROCESSED_DIR = "processed_dataset"
MODEL_DIR = "models"

def compute_incremental_stats():
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # 1. Flow Scaler
    print("Computing Flow Scaler (Incremental)...")
    flow_scaler = StandardScaler()
    flow_files = glob.glob(os.path.join(PROCESSED_DIR, "**", "*_flows.parquet"), recursive=True)
    
    # Exclude non-feature columns
    exclude_cols = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 'timestamp_min', 'timestamp_max', 'label']
    
    for f in tqdm(flow_files, desc="Flows"):
        try:
            df = pd.read_parquet(f)
            features = df.drop(columns=[c for c in exclude_cols if c in df.columns])
            flow_scaler.partial_fit(features)
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    joblib.dump(flow_scaler, os.path.join(MODEL_DIR, "flow_scaler.joblib"))
    print(f"Flow Scaler saved. Features: {flow_scaler.n_features_in_}")

    # 2. Sequence Scaler
    print("\nComputing Sequence Scaler (Incremental)...")
    seq_scaler = StandardScaler()
    seq_files = glob.glob(os.path.join(PROCESSED_DIR, "**", "*_sequences.parquet"), recursive=True)
    
    for f in tqdm(seq_files, desc="Sequences"):
        try:
            df = pd.read_parquet(f)
            # Sequences are flattened 1800-dim vectors (200 packets x 9 features)
            # We want to normalize the 9 features uniformly across the 200 time steps
            # So we reshape to (-1, 9) to get global mean/std per feature type
            seq_data = np.stack(df['sequence_features'].values) # (N, 1800)
            seq_data_reshaped = seq_data.reshape(-1, 9) # (N*200, 9)
            seq_scaler.partial_fit(seq_data_reshaped)
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    joblib.dump(seq_scaler, os.path.join(MODEL_DIR, "seq_scaler.joblib"))
    print(f"Sequence Scaler saved. Features: {seq_scaler.n_features_in_}")

if __name__ == "__main__":
    compute_incremental_stats()
