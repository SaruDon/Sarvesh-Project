import pandas as pd
import os
import glob
from tqdm import tqdm

def debug_network(day_dir):
    files = glob.glob(os.path.join(day_dir, "*_flows.parquet"))
    target_date = pd.to_datetime("2018-03-02").date()
    
    print(f"Finding files on {target_date}...")
    target_files = []
    for f in files:
        df = pd.read_parquet(f, columns=['timestamp_min'])
        if df['timestamp_min'].iloc[0].date() == target_date:
            target_files.append(f)
            
    print(f"Found {len(target_files)} files on target date.")
    if not target_files: return

    # Check first target file
    f = target_files[0]
    print(f"\nChecking sample file: {os.path.basename(f)}")
    df = pd.read_parquet(f)
    print(f"Unique Source IPs: {df['ip.src'].unique()[:10]}")
    print(f"Unique Dest IPs: {df['ip.dst'].unique()[:10]}")
    
    # Check if target IP 192.168.10.15 appears AT ALL
    target_ip = "192.168.10.15"
    has_target = ((df['ip.src'] == target_ip) | (df['ip.dst'] == target_ip)).any()
    print(f"Target IP {target_ip} present in this file: {has_target}")

if __name__ == "__main__":
    debug_network("processed_dataset/Friday-02-03-2018")
