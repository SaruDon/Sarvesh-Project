import pandas as pd
import glob
import os

processed_dir = "processed_dataset"
days = ["Thursday-01-03-2018", "Thursday-22-02-2018", "Thursday-15-02-2018", "Wednesday-21-02-2018"]

print(f"{'Day':<25} | {'Label':<20} | {'Count':<10}")
print("-" * 60)

for day in days:
    path = os.path.join(processed_dir, day, "*_flows.parquet")
    files = glob.glob(path)
    if not files:
        print(f"{day:<25} | {'No data found':<20} | {'-':<10}")
        continue
        
    all_labels = []
    for f in files:
        df = pd.read_parquet(f, columns=['label'])
        all_labels.append(df['label'].value_counts())
    
    if all_labels:
        counts = pd.concat(all_labels).groupby(level=0).sum()
        for label, count in counts.items():
            print(f"{day:<25} | {label:<20} | {count:<10}")
    else:
        print(f"{day:<25} | {'No labels found':<20} | {'-':<10}")
