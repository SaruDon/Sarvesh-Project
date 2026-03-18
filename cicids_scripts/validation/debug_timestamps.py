import pandas as pd
import glob
import os

def check_timestamps(day_dir):
    files = glob.glob(os.path.join(day_dir, "*_flows.parquet"))
    if not files:
        print("No files found!")
        return
        
    print(f"Checking {len(files)} files for timestamp ranges...")
    
    unique_dates = set()
    overall_min = None
    overall_max = None
    
    for f in files:
        df = pd.read_parquet(f, columns=['timestamp_min', 'timestamp_max'])
        f_min = df['timestamp_min'].min()
        f_max = df['timestamp_max'].max()
        
        if overall_min is None or f_min < overall_min: overall_min = f_min
        if overall_max is None or f_max > overall_max: overall_max = f_max
        
        unique_dates.add(f_min.date())
        unique_dates.add(f_max.date())
        
    print(f"Unique Dates Found: {unique_dates}")
    print(f"Overall Min Timestamp: {overall_min}")
    print(f"Overall Max Timestamp: {overall_max}")

if __name__ == "__main__":
    check_timestamps("processed_dataset/Friday-02-03-2018")
