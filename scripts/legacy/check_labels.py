import pandas as pd
import glob
import os

processed_dir = r"c:\Users\Student\.gemini\antigravity\scratch\sarvesh-project\processed_dataset\Friday-16-02-2018"
files = glob.glob(os.path.join(processed_dir, "*_flows.parquet"))

if not files:
    print("No flow files found.")
else:
    # Read all files to see if DDoS labels exist
    count_files_with_ddos = 0
    total_ddos_rows = 0
    for f in files:
        df = pd.read_parquet(f)
        label_cols = [c for c in df.columns if 'label' in c.lower()]
        if label_cols:
            counts = df[label_cols[0]].value_counts()
            ddos_rows = sum(c for label, c in counts.items() if 'DDoS' in str(label))
            if ddos_rows > 0:
                print(f"[{os.path.basename(f)}] {dict(counts)}")
                count_files_with_ddos += 1
                total_ddos_rows += ddos_rows
    
    print(f"\nFinal Summary:")
    print(f"Files with DDoS: {count_files_with_ddos} / {len(files)}")
    print(f"Total DDoS Flow rows: {total_ddos_rows}")
