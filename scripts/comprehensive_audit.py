import pandas as pd
import glob
import os

processed_dir = "processed_dataset"
days = [d for d in os.listdir(processed_dir) if os.path.isdir(os.path.join(processed_dir, d))]
days.sort()

print(f"{'Day':<25} | {'Label':<25} | {'Count':<10}")
print("-" * 70)

total_rows = 0
for day in days:
    path = os.path.join(processed_dir, day, "*_flows.parquet")
    files = glob.glob(path)
    if not files:
        # Check if it's the 'pcap' or 'Golden_Test_Set' folder which we expect
        if day in ['pcap', 'Golden_Test_Set']:
            continue
        print(f"{day:<25} | {'No parquet files found':<25} | {'-':<10}")
        continue
        
    all_labels = []
    for f in files:
        try:
            # First read schema to see which label column exists
            df_head = pd.read_parquet(f, columns=None)
            label_col = 'label' if 'label' in df_head.columns else 'label_<lambda>'
            if label_col not in df_head.columns:
                print(f"No label column found in {f}. Columns: {df_head.columns.tolist()}")
                continue
                
            df = pd.read_parquet(f, columns=[label_col])
            counts_f = df[label_col].value_counts()
            all_labels.append(counts_f)
        except Exception as e:
            print(f"Error reading {f}: {e}")
    
    if all_labels:
        counts = pd.concat(all_labels).groupby(level=0).sum()
        for label, count in counts.items():
            print(f"{day:<25} | {label:<25} | {count:<10}")
            total_rows += count
    else:
        print(f"{day:<25} | {'No data in parquets':<25} | {'-':<10}")

# Also check for loose files in processed_dataset root
loose_files = glob.glob(os.path.join(processed_dir, "*.parquet"))
if loose_files:
    print("\nLoose files in processed_dataset root:")
    for f in loose_files:
        print(f"  - {os.path.basename(f)}")

print("-" * 70)
print(f"{'TOTAL ROWS':<25} | {'':<25} | {total_rows:<10}")
