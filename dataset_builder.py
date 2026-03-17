import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import os
import glob
from tqdm import tqdm

# Configuration
INPUT_DIR = "extracted_features"
OUTPUT_DIR = "processed_dataset"
ATTACK_LOGS = "attack_logs.csv"
WINDOW_SIZE = 200
STRIDE = 50
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
            mask = mask & ((df['ip.src'] == row['Target_IP']) | (df['ip.dst'] == row['Target_IP']))
            
        df.loc[mask, 'label'] = row['Attack_Type']
    return df

def build_labeled_dataset():
    print(f"Loading attack logs from {ATTACK_LOGS}...")
    attack_logs = parse_attack_logs(ATTACK_LOGS)
    if attack_logs is None:
        print("Attack logs not found. Proceeding without labels.")

    # Recursive search for CSV files
    csv_files = []
    for root, _, files in os.walk(INPUT_DIR):
        for f in files:
            if f.endswith(".csv"):
                csv_files.append(os.path.join(root, f))
                
    if not csv_files:
        print(f"No CSV files found in {INPUT_DIR}. Please run extraction first.")
        return

    for file_path in tqdm(csv_files, desc="Building datasets"):
        file_name = os.path.basename(file_path)
        
        # Determine relative subdirectory to maintain structure
        rel_path = os.path.relpath(os.path.dirname(file_path), INPUT_DIR)
        target_dir = os.path.join(OUTPUT_DIR, rel_path)
        os.makedirs(target_dir, exist_ok=True)
        
        print(f"\nProcessing {file_name} in {rel_path}...")
        
        try:
            df = pd.read_csv(file_path)
            
            if 'frame.time_epoch' not in df.columns:
                print(f"Skipping {file_name}: No frame.time_epoch found.")
                continue
                
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
            
            # Approximate payload length ratio (assuming standard IPv4 + TCP headers = ~40 bytes)
            df['payload_ratio'] = np.where(df['frame.len'] > 40, (df['frame.len'] - 40) / df['frame.len'], 0.0)

            print("  Building Flow Dataset (XGBoost)...")
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
            flows['flow_duration_sec'] = (flows['timestamp_max'] - flows['timestamp_min']).dt.total_seconds()
            flows['packet_rate'] = flows['frame.len_count'] / flows['flow_duration_sec'].replace(0, 0.001)
            
            flow_output = os.path.join(target_dir, f"{file_name.replace('.csv', '')}_flows.parquet")
            flows.to_parquet(flow_output)
            print(f"  -> Saved {len(flows)} flows to {flow_output}")

            print("  Building Session-based Sequence Dataset (Transformer)...")
            # 3. Session Sequence Generation with Sliding Windows
            session_cols = ['ip.src', 'ip.dst']
            seq_features = ['frame.len', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 
                            'tcp.flags', 'ip.ttl', 'tcp.window_size_value', 'packet_direction', 'payload_ratio']
            
            all_sequences = []
            all_labels = []
            
            for session_id, group in tqdm(df.groupby(session_cols), desc="  Extracting Sequences", leave=False):
                group = group.sort_values('timestamp').copy()
                initiator = group['ip.src'].iloc[0]
                group['packet_direction'] = (group['ip.src'] == initiator).astype(int)
                
                if len(group) <= WINDOW_SIZE:
                    seq_data = group[seq_features].fillna(0).values
                    if len(seq_data) < WINDOW_SIZE:
                        pad = np.zeros((WINDOW_SIZE - len(seq_data), len(seq_features)))
                        seq_data = np.vstack([seq_data, pad])
                    all_sequences.append(seq_data)
                    all_labels.append(group['label'].mode()[0])
                else:
                    for start_idx in range(0, len(group) - WINDOW_SIZE + 1, STRIDE):
                        window = group.iloc[start_idx : start_idx + WINDOW_SIZE]
                        seq_data = window[seq_features].fillna(0).values
                        all_sequences.append(seq_data)
                        all_labels.append(window['label'].mode()[0])

            seq_df = pd.DataFrame({
                'sequence_features': [seq.tolist() for seq in all_sequences],
                'label': all_labels
            })
            
            seq_output = os.path.join(target_dir, f"{file_name.replace('.csv', '')}_sequences.parquet")
            seq_df.to_parquet(seq_output)
            print(f"  -> Saved {len(seq_df)} sliding-window sequences to {seq_output}")

        except Exception as e:
            print(f"Error processing {file_name}: {e}")

if __name__ == "__main__":
    build_labeled_dataset()

