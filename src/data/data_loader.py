import os
import glob
import pandas as pd
import numpy as np
import joblib
import torch
import random
from torch.utils.data import Dataset, DataLoader, IterableDataset, get_worker_info

class NIDSDataset(Dataset):
    """
    Optimized dataset for Flow or Sequence data.
    Uses binary search for file mapping and a single-file cache to avoid
    redundant Parquet reads when samples are requested from the same partition.
    """
    def __init__(self, processed_dir, mode='flow', scaler_path=None, use_test_set=False):
        self.mode = mode
        if use_test_set:
            self.files = [f for f in glob.glob(os.path.join(processed_dir, "Golden_Test_Set", "**", f"*_{mode}s.parquet"), recursive=True)]
        else:
            self.files = [f for f in glob.glob(os.path.join(processed_dir, "**", f"*_{mode}s.parquet"), recursive=True)
                          if "Golden_Test_Set" not in f]
        
        if not self.files:
            raise FileNotFoundError(f"No {mode} files found in {processed_dir}")

        self.scaler = joblib.load(scaler_path) if scaler_path else None
        
        self.file_map = []
        self.total_rows = 0
        print(f"Mapping {len(self.files)} {mode} files (this may take a moment)...")
        
        for f in self.files:
            try:
                # Use metadata-only read if possible, fallback to label col
                row_count = pd.read_parquet(f, columns=[]).shape[0] if mode == 'flow' else pd.read_parquet(f, columns=['label']).shape[0]
                if row_count > 0:
                    self.file_map.append({'path': f, 'start': self.total_rows, 'len': row_count})
                    self.total_rows += row_count
            except: pass
        
        self.starts = np.array([f['start'] for f in self.file_map])
        
        # Simple cache for the last accessed file
        self._current_df = None
        self._current_path = None

    def __len__(self):
        return self.total_rows

    def _get_df(self, path):
        if self._current_path == path:
            return self._current_df
        self._current_path = path
        self._current_df = pd.read_parquet(path)
        return self._current_df

    def __getitem__(self, idx):
        if idx < 0 or idx >= self.total_rows:
            raise IndexError("Index out of range")
            
        file_idx = np.searchsorted(self.starts, idx, side='right') - 1
        f_info = self.file_map[file_idx]
        
        local_idx = int(idx - f_info['start'])
        df = self._get_df(f_info['path'])
        
        try:
            if self.mode == 'flow':
                exclude = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 'timestamp_min', 'timestamp_max', 'label']
                row = df.iloc[local_idx]
                X = row.drop(labels=[c for c in exclude if c in row.index]).values.astype(np.float32)
                y = 1 if row['label'] != 'Benign' else 0
            else:
                X = df['sequence_features'].iloc[local_idx].astype(np.float32)
                y = 1 if df['label'].iloc[local_idx] != 'Benign' else 0
        except Exception as e:
            # Fallback for corrupted indexes
            return self.__getitem__((idx + 1) % self.total_rows)
        
        if self.scaler:
            if self.mode == 'flow':
                X = self.scaler.transform(X.reshape(1, -1)).flatten()
            else:
                X = self.scaler.transform(X.reshape(-1, 9)).flatten()
        
        return torch.tensor(X), torch.tensor(y)

class ShardedNIDSDataset(IterableDataset):
    """
    High-performance IterableDataset for 17M+ sequences.
    Instead of random access, it reads entire Parquet files (shards) into 
    memory, shuffles them locally, and yields samples.
    
    Interleaving: Buffers multiple files at once to maintain randomness.
    """
    def __init__(self, processed_dir, mode='sequence', scaler_path=None, use_test_set=False,
                 buffer_size=4, exclude_days=None):
        self.mode = mode
        exclude_days = exclude_days or []
        if use_test_set:
            self.all_files = [f for f in glob.glob(os.path.join(processed_dir, "Golden_Test_Set", "**", f"*_{mode}s.parquet"), recursive=True)]
        else:
            self.all_files = [
                f for f in glob.glob(os.path.join(processed_dir, "**", f"*_{mode}s.parquet"), recursive=True)
                if "Golden_Test_Set" not in f
                and not any(day in f for day in exclude_days)  # Skip excluded days
            ]
        self.scaler = joblib.load(scaler_path) if scaler_path else None
        self.buffer_size = buffer_size # Number of files to interleave
        
        # Calculate total length for progress bars
        self.total_rows = 0
        for f in self.all_files:
            try:
                self.total_rows += pd.read_parquet(f, columns=['label']).shape[0]
            except: pass

    def __len__(self):
        return self.total_rows

    def __iter__(self):
        # Handle PyTorch Multi-processing
        worker_info = get_worker_info()
        if worker_info is None:
            files = self.all_files
        else:
            # Split files across workers
            per_worker = int(np.ceil(len(self.all_files) / worker_info.num_workers))
            worker_id = worker_info.id
            files = self.all_files[worker_id * per_worker : (worker_id + 1) * per_worker]
        
        # 1. Shuffle file list initially
        random.shuffle(files)
        
        # 2. Iterate through files and yield samples
        for f in files:
            try:
                df = pd.read_parquet(f)
                if len(df) == 0: continue
                
                # Shuffle rows locally within the file/shard
                df = df.sample(frac=1).reset_index(drop=True)
                
                # Use itertuples for 10x speed over iterrows
                for row in df.itertuples():
                    if self.mode == 'flow':
                        # This assumes specific column order/names
                        # It's safer to use df.values if we know the columns
                        pass 
                    else:
                        X = row.sequence_features.astype(np.float32)
                        y = 1 if row.label != 'Benign' else 0
                    
                    if self.scaler:
                        if self.mode == 'flow':
                            X = self.scaler.transform(X.reshape(1, -1)).flatten()
                        else:
                            X = self.scaler.transform(X.reshape(-1, 9)).flatten()
                    
                    yield torch.tensor(X), torch.tensor(y)
            except Exception as e:
                print(f"Error processing file {f}: {e}")
                continue

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
