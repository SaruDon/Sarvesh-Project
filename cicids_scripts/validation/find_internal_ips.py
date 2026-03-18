import pandas as pd
import os
import glob
from collections import Counter

def find_active_internal_ips(day_dir):
    flow_files = glob.glob(os.path.join(day_dir, "*_flows.parquet"))
    # Filter for March 2nd
    target_date = pd.to_datetime("2018-03-02").date()
    
    internal_counts = Counter()
    print("Sampling internal IPs from March 2nd files...")
    
    for f in flow_files[:50]: # Sample 50 files
        df = pd.read_parquet(f, columns=['ip.src', 'ip.dst', 'timestamp_min'])
        if df['timestamp_min'].iloc[0].date() != target_date: continue
        
        # Source IPs that are internal
        src_internal = df[df['ip.src'].str.startswith('172.31.', na=False)]['ip.src']
        dst_internal = df[df['ip.dst'].str.startswith('172.31.', na=False)]['ip.dst']
        
        internal_counts.update(src_internal.tolist())
        internal_counts.update(dst_internal.tolist())
        
    print("\nMost active internal IPs on March 2nd:")
    for ip, count in internal_counts.most_common(20):
        print(f"  {ip}: {count}")

if __name__ == "__main__":
    find_active_internal_ips("processed_dataset/Friday-02-03-2018")
