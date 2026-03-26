import pandas as pd
import glob
import os
import sys
from collections import Counter

def diagnose():
    day = sys.argv[1] if len(sys.argv) > 1 else "Friday-16-02-2018"
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(BASE_DIR, "processed_dataset", day)
    files = glob.glob(os.path.join(processed_dir, "*_flows.parquet"))

    if not files:
        print(f"No files found for {day} in {processed_dir}")
        return
        
    min_time = None
    max_time = None
    
    # We investigate the most targeted internal IPs
    target_counts = Counter()
    
    print(f"Analyzing {len(files)} files for {day}...")
    for f in files:
        df = pd.read_parquet(f)
        
        # Track time range
        cur_min = df['timestamp_min'].min()
        cur_max = df['timestamp_min'].max()
        if min_time is None or cur_min < min_time: min_time = cur_min
        if max_time is None or cur_max > max_time: max_time = cur_max
        
        # Track internal targets
        internal_dst = df[df['ip.dst'].str.startswith('172.31.', na=False)]
        if not internal_dst.empty:
            target_counts.update(internal_dst['ip.dst'].tolist())
            
    print(f"\n--- Diagnostic Report for {day} ---")
    print(f"Total Time range (UTC): {min_time} to {max_time}")
    print(f"Top 5 Internal Targets:\n{target_counts.most_common(5)}")
    
    if target_counts:
        top_victim = target_counts.most_common(1)[0][0]
        print(f"\nAnalyzing high-resolution spike for top victim: {top_victim}")
        
        time_series = []
        for f in files:
            df = pd.read_parquet(f)
            victim_traffic = df[df['ip.dst'] == top_victim]
            if not victim_traffic.empty:
                victim_traffic['minute'] = victim_traffic['timestamp_min'].dt.floor('min')
                time_series.append(victim_traffic['minute'].value_counts())
        
        if time_series:
            full_series = pd.concat(time_series).groupby(level=0).sum().sort_index()
            print(f"Top 10 Busiest Minutes for {top_victim}:")
            print(full_series.sort_values(ascending=False).head(10))

if __name__ == "__main__":
    diagnose()
