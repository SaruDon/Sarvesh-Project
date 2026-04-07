import os
import glob
import pandas as pd
import numpy as np
import joblib
import torch
from torch.utils.data import Dataset, DataLoader

class NIDSDataset(Dataset):
    """Streaming dataset for Flow or Sequence data."""
    def __init__(self, processed_dir, mode='flow', scaler_path=None, use_test_set=False):
        self.mode = mode
        if use_test_set:
            self.files = [f for f in glob.glob(os.path.join(processed_dir, "Golden_Test_Set", "**", f"*_{mode}s.parquet"), recursive=True)]
        else:
            self.files = [f for f in glob.glob(os.path.join(processed_dir, "**", f"*_{mode}s.parquet"), recursive=True)
                          if "Golden_Test_Set" not in f]
        self.scaler = joblib.load(scaler_path) if scaler_path else None
        
        # Pre-calculate row indices for each file to allow random access across files
        # For 51M flows, this meta-map must be light
        self.file_map = []
        self.total_rows = 0
        print(f"Mapping {len(self.files)} {mode} files...")
        
        for f in self.files:
            try:
                # Get shape only (fast)
                row_count = pd.read_parquet(f, columns=['label']).shape[0]
                self.file_map.append({'path': f, 'start': self.total_rows, 'len': row_count})
                self.total_rows += row_count
            except: pass

    def __len__(self):
        return self.total_rows

    def __getitem__(self, idx):
        # Find which file contains the index
        for f_info in self.file_map:
            if f_info['start'] <= idx < f_info['start'] + f_info['len']:
                local_idx = int(idx - f_info['start'])
                df = pd.read_parquet(f_info['path'])
                
                if self.mode == 'flow':
                    exclude = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 'timestamp_min', 'timestamp_max', 'label']
                    X = df.drop(columns=[c for c in exclude if c in df.columns]).iloc[local_idx].values.astype(np.float32)
                    y = 1 if df['label'].iloc[local_idx] != 'Benign' else 0
                else:
                    X = df['sequence_features'].iloc[local_idx].astype(np.float32)
                    y = 1 if df['label'].iloc[local_idx] != 'Benign' else 0
                
                if self.scaler:
                    if self.mode == 'flow':
                        X = self.scaler.transform(X.reshape(1, -1)).flatten()
                    else:
                        X = self.scaler.transform(X.reshape(-1, 9)).flatten()
                
                return torch.tensor(X), torch.tensor(y)
        
        raise IndexError("Index out of range")

def get_parquet_chunks(processed_dir, mode='flow', chunk_size=100000, scaler_path=None):
    """Generator for XGBoost-style chunked training."""
    files = glob.glob(os.path.join(processed_dir, "**", f"*_{mode}s.parquet"), recursive=True)
    scaler = joblib.load(scaler_path) if scaler_path else None
    
    for f in files:
        try:
            df = pd.read_parquet(f)
            if mode == 'flow':
                exclude = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 'timestamp_min', 'timestamp_max', 'label']
                X = df.drop(columns=[c for c in exclude if c in df.columns]).astype(np.float32)
                y = (df['label'] != 'Benign').astype(int)
            else:
                X = np.stack(df['sequence_features'].values)
                y = (df['label'] != 'Benign').astype(int)
                
            if scaler:
                if mode == 'flow':
                    X[:] = scaler.transform(X)
                else:
                    # (N, 1800) -> (N*200, 9) -> transform -> (N, 1800)
                    X_reshaped = X.reshape(-1, 9)
                    X_scaled = scaler.transform(X_reshaped)
                    X = X_scaled.reshape(X.shape)
            
            # Yield in smaller chunks to avoid large memory spikes
            for i in range(0, len(X), chunk_size):
                yield X[i:i+chunk_size], y[i:i+chunk_size]
        except Exception as e:
            print(f"Error loading {f}: {e}")
            continue
