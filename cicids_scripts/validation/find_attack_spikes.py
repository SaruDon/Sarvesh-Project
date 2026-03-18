import pandas as pd
import os
import glob
from tqdm import tqdm

def find_spikes(day_dir):
    files = glob.glob(os.path.join(day_dir, "*_flows.parquet"))
    target_date = pd.to_datetime("2018-03-02").date()
    
    print(f"Analyzing {len(files)} files for traffic spikes on {target_date}...")
    
    time_bins = {}
    
    for f in tqdm(files, desc="Binning traffic"):
        # Select only necessary columns to save memory
        df = pd.read_parquet(f, columns=['timestamp_min', 'frame.len_count'])
        df['hour'] = df['timestamp_min'].dt.hour
        
        for hour, count in df.groupby('hour')['frame.len_count'].sum().items():
            time_bins[hour] = time_bins.get(hour, 0) + count
            
    print("\nTraffic Distribution (Hourly UTC):")
    for hour in sorted(time_bins.keys()):
        print(f"  {hour:02d}:00 - {time_bins[hour]:,}")

if __name__ == "__main__":
    find_spikes("processed_dataset/Friday-02-03-2018")
