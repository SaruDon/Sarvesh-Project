import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import os
import glob
from tqdm import tqdm
import multiprocessing as mp
from functools import partial
import argparse

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "extracted_features")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed_dataset")
ATTACK_LOGS = os.path.join(BASE_DIR, "data", "attack_logs.csv")
WINDOW_SIZE = 200
STRIDE = 50
MAX_SEQS_PER_FILE = 50000 
DEFAULT_WORKERS = 10

def parse_attack_logs(log_path):
    if not os.path.exists(log_path):
        return None
    logs = pd.read_csv(log_path)
    logs['start'] = pd.to_datetime(logs['Date'] + ' ' + logs['Start_Time'])
    logs['end'] = pd.to_datetime(logs['Date'] + ' ' + logs['End_Time'])
    return logs

def apply_labels(df, attack_logs):
    df['label'] = 'Benign'
    if attack_logs is None:
        return df
    
    for _, row in attack_logs.iterrows():
        mask = (df['timestamp'] >= row['start']) & (df['timestamp'] <= row['end'])
        
        if 'Target_IP' in row and pd.notna(row['Target_IP']):
            mask = mask & ((df['ip.src'].str.startswith(str(row['Target_IP']), na=False)) | (df['ip.dst'].str.startswith(str(row['Target_IP']), na=False)))
            
        df.loc[mask, 'label'] = row['Attack_Type']
    return df

def process_single_csv(file_path, attack_logs, force=False):
    file_name = os.path.basename(file_path)
    # Determine relative subdirectory to maintain structure
    rel_path = os.path.relpath(os.path.dirname(file_path), INPUT_DIR)
    target_dir = os.path.join(OUTPUT_DIR, rel_path)
    os.makedirs(target_dir, exist_ok=True)
    
    flow_output = os.path.join(target_dir, f"{file_name.replace('.csv', '')}_flows.parquet")
    seq_output = os.path.join(target_dir, f"{file_name.replace('.csv', '')}_sequences.parquet")

    # Skip if both outputs exist, unless force is True
    if not force and os.path.exists(flow_output) and os.path.exists(seq_output):
        return f"Skipped {file_name} (already processed)"

    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='utf-16')
        
        if 'frame.time_epoch' not in df.columns:
            return f"Skipped {file_name}: No frame.time_epoch found."
            
        df['timestamp'] = pd.to_datetime(df['frame.time_epoch'], unit='s', errors='coerce')
        df = df.dropna(subset=['timestamp'])
        df = df.sort_values('timestamp')
        
        # Ensure numeric types for aggregation
        numeric_cols = ['frame.len', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 'ip.ttl', 'tcp.window_size_value']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 1. Labeling
        df = apply_labels(df, attack_logs)
        
        # Feature filling
        fill_cols = ['ip.proto', 'tcp.srcport', 'tcp.dstport', 'ip.ttl', 'tcp.window_size_value']
        for col in fill_cols:
            if col not in df.columns:
                df[col] = 0
        df[fill_cols] = df[fill_cols].fillna(0)
        
        # Convert tcp.flags from hex string (e.g. "0x0002") to integer
        if 'tcp.flags' not in df.columns:
            df['tcp.flags'] = 0
        else:
            df['tcp.flags'] = df['tcp.flags'].apply(
                lambda x: int(str(x), 16) if pd.notna(x) and str(x).startswith('0x') else (int(x) if pd.notna(x) and str(x).isdigit() else 0)
            )
        
        # Approximate payload length ratio
        df['payload_ratio'] = np.where(df['frame.len'] > 40, (df['frame.len'] - 40) / df['frame.len'], 0.0)

        # 2. Flow Aggregation (XGBoost)
        flow_cols = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport']
        flows = df.groupby(flow_cols).agg({
            'frame.len': ['count', 'sum', 'mean', 'std'],
            'timestamp': ['min', 'max'],
            'ip.ttl': ['mean'],
            'tcp.window_size_value': ['mean'],
            'label': lambda x: x.mode()[0] if not x.mode().empty else 'Benign'
        }).reset_index()
        
        flows.columns = ['_'.join(col).strip() if isinstance(col, tuple) and col[1] else col[0] for col in flows.columns.values]
        if 'label_<lambda>' in flows.columns:
            flows = flows.rename(columns={'label_<lambda>': 'label'})

        flows['flow_duration_sec'] = (flows['timestamp_max'] - flows['timestamp_min']).dt.total_seconds()
        flows['packet_rate'] = flows['frame.len_count'] / flows['flow_duration_sec'].replace(0, 0.001)
        
        flows.to_parquet(flow_output)

        # 3. Session Sequence Generation (Transformer)
        session_cols = ['ip.src', 'ip.dst']
        seq_features = ['frame.len', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 
                        'tcp.flags', 'ip.ttl', 'tcp.window_size_value', 'packet_direction', 'payload_ratio']
        
        all_sequences = []
        all_labels = []
        
        for session_id, group in df.groupby(session_cols):
            if len(all_sequences) >= MAX_SEQS_PER_FILE: break
                
            group = group.sort_values('timestamp').copy()
            initiator = group['ip.src'].iloc[0]
            group['packet_direction'] = (group['ip.src'] == initiator).astype(int)
            
            if len(group) <= WINDOW_SIZE:
                seq_data = group[seq_features].fillna(0).astype(np.float32).values
                if len(seq_data) < WINDOW_SIZE:
                    pad = np.zeros((WINDOW_SIZE - len(seq_data), len(seq_features)), dtype=np.float32)
                    seq_data = np.vstack([seq_data, pad])
                all_sequences.append(seq_data.flatten())
                all_labels.append(group['label'].mode()[0])
            else:
                for start_idx in range(0, len(group) - WINDOW_SIZE + 1, STRIDE):
                    if len(all_sequences) >= MAX_SEQS_PER_FILE: break
                    window = group.iloc[start_idx : start_idx + WINDOW_SIZE]
                    seq_data = window[seq_features].fillna(0).astype(np.float32).values
                    all_sequences.append(seq_data.flatten())
                    all_labels.append(window['label'].mode()[0])

        if all_sequences:
            seq_df = pd.DataFrame({
                'sequence_features': all_sequences,
                'label': all_labels
            })
            seq_df.to_parquet(seq_output)
            
        return f"Success: {file_name} ({len(flows)} flows, {len(all_sequences)} sequences)"

    except Exception as e:
        return f"Error processing {file_name}: {e}"

def build_labeled_dataset(workers=DEFAULT_WORKERS, limit=None, day_filter=None, force=False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Loading attack logs from {ATTACK_LOGS}...")
    attack_logs = parse_attack_logs(ATTACK_LOGS)

    csv_files = []
    for root, _, files in os.walk(INPUT_DIR):
        if day_filter and day_filter not in root:
            continue
        for f in files:
            if f.endswith(".csv"):
                csv_files.append(os.path.join(root, f))
                
    # Prioritize if no filter
    if not day_filter:
        csv_files.sort(key=lambda x: "Friday-02-03-2018" not in x)
    else:
        print(f"Filtering for day: {day_filter}")
    
    if limit:
        csv_files = csv_files[:limit]
                
    if not csv_files:
        print(f"No CSV files found in {INPUT_DIR} (Filter: {day_filter}).")
        return

    print(f"Found {len(csv_files)} files. Starting parallel processing with {workers} workers...")
    
    # Use partial to pass attack_logs and force flag
    worker_func = partial(process_single_csv, attack_logs=attack_logs, force=force)
    
    with mp.Pool(processes=workers) as pool:
        # Use imap_unordered for better feedback with tqdm
        results = list(tqdm(pool.imap_unordered(worker_func, csv_files), total=len(csv_files), desc="Building datasets"))

    # Summary
    success_count = sum(1 for r in results if r.startswith("Success"))
    error_count = sum(1 for r in results if r.startswith("Error"))
    skipped_count = sum(1 for r in results if r.startswith("Skipped"))
    
    print(f"\nProcessing Complete:")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors:  {error_count}")
    
    if error_count > 0:
        print("\nErrors encountered:")
        for r in results:
            if r.startswith("Error"):
                print(f"  - {r}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parallel Dataset Builder")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Number of parallel workers")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files to process")
    parser.add_argument("--day", type=str, default=None, help="Process only specific day folder")
    parser.add_argument("--force", action="store_true", help="Overwrite existing parquet files")
    args = parser.parse_args()
    
    build_labeled_dataset(workers=args.workers, limit=args.limit, day_filter=args.day, force=args.force)
