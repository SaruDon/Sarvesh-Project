import pandas as pd
import os
import numpy as np
from tqdm import tqdm

# Configuration
INPUT_FILE = r"extracted_features\Tuesday-20-02-2018\UCAP172.31.69.25.csv"
OUTPUT_DIR = r"processed_dataset\Tuesday-20-02-2018"
ATTACK_LOGS = r"data\attack_logs.csv"
CHUNK_SIZE = 1000000 # 1 Million rows at a time
BASE_NAME = "UCAP172.31.69.25"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_attack_logs(log_path):
    logs = pd.read_csv(log_path)
    logs = logs[logs['Date'] == '2018-02-20']
    logs['start'] = pd.to_datetime(logs['Date'] + ' ' + logs['Start_Time'])
    logs['end'] = pd.to_datetime(logs['Date'] + ' ' + logs['End_Time'])
    return logs

def process_massive_csv():
    logs = parse_attack_logs(ATTACK_LOGS)
    print(f"Loaded {len(logs)} attack windows for Tuesday-20.")
    print(f"Processing {INPUT_FILE} in chunks of {CHUNK_SIZE}...")

    # Iterate in chunks
    chunk_idx = 0
    reader = pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE, encoding='utf-8-sig', on_bad_lines='skip')
    
    for chunk in tqdm(reader, desc="Processing chunks"):
        if 'frame.time_epoch' not in chunk.columns:
            continue
            
        chunk['timestamp'] = pd.to_datetime(chunk['frame.time_epoch'], unit='s', errors='coerce')
        chunk = chunk.dropna(subset=['timestamp'])
        
        # Labeling
        chunk['label'] = 'Benign'
        for _, row in logs.iterrows():
            mask = (chunk['timestamp'] >= row['start']) & (chunk['timestamp'] <= row['end'])
            if 'Target_IP' in row and pd.notna(row['Target_IP']):
                 mask = mask & ((chunk['ip.src'].str.startswith(str(row['Target_IP']), na=False)) | (chunk['ip.dst'].str.startswith(str(row['Target_IP']), na=False)))
            chunk.loc[mask, 'label'] = row['Attack_Type']
            
        # Simplified Flow Aggregation for the massive file to save memory
        chunk['payload_ratio'] = np.where(chunk['frame.len'] > 40, (chunk['frame.len'] - 40) / chunk['frame.len'], 0.0)
        
        # Convert numeric
        for col in ['frame.len', 'ip.proto', 'tcp.srcport', 'tcp.dstport', 'ip.ttl']:
            chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0)

        # Aggregate flows in this chunk
        flow_cols = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport']
        flows = chunk.groupby(flow_cols).agg({
            'frame.len': ['count', 'sum', 'mean', 'std'],
            'timestamp': ['min', 'max'],
            'ip.ttl': 'mean',
            'label': lambda x: x.mode()[0] if not x.empty else 'Benign'
        })
        
        flows.columns = [f"{c[0]}_{c[1]}" if isinstance(c, tuple) else c for c in flows.columns]
        flows = flows.reset_index()
        flows = flows.rename(columns={'label_<lambda>': 'label'})
        
        # Save chunk result
        output_file = os.path.join(OUTPUT_DIR, f"{BASE_NAME}_part{chunk_idx}_flows.parquet")
        flows.to_parquet(output_file)
        
        chunk_idx += 1

    print(f"Massive processing complete. Generated {chunk_idx} parquet files.")

if __name__ == "__main__":
    process_massive_csv()
