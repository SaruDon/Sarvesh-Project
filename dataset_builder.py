import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os
import glob
from tqdm import tqdm

# Configuration
INPUT_DIR = "extracted_features"
OUTPUT_DIR = "processed_dataset"
ATTACK_LOGS = "attack_logs.csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_labeled_dataset():
    print(f"Loading attack logs from {ATTACK_LOGS}...")
    if os.path.exists(ATTACK_LOGS):
        logs = pd.read_csv(ATTACK_LOGS)
    else:
        print("Attack logs not found. Proceeding without labels.")
        logs = None

    csv_files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {INPUT_DIR}. Please run extraction first.")
        return

    for file_path in tqdm(csv_files, desc="Building datasets"):
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...")
        
        try:
            df = pd.read_csv(file_path)
            
            # 1. Labeling Logic (Simple implementation based on attack schedule)
            # This is a placeholder for more complex temporal labeling
            df['label'] = 'Benign'
            
            # 2. Flow Aggregation (Example features for XGBoost)
            # Grouping by 5-tuple: (src, dst, proto, srcport, dstport)
            # We'll use the available columns from tshark extraction
            group_cols = ['ip.src', 'ip.dst', 'ip.proto', 'tcp.srcport', 'tcp.dstport']
            # Fill NaNs for ports (UDP uses different names in tshark usually, let's handle if available)
            for col in group_cols:
                if col not in df.columns:
                    df[col] = 0
            
            flows = df.groupby(group_cols).agg({
                'frame.len': ['count', 'sum', 'mean', 'std'],
                'frame.time_relative': ['min', 'max']
            }).reset_index()
            
            # Flatten columns
            flows.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in flows.columns.values]
            
            # 3. Save as Parquet (Efficient for large data)
            output_file = os.path.join(OUTPUT_DIR, f"{file_name.replace('.csv', '')}_flows.parquet")
            flows.to_parquet(output_file)
            print(f"Saved flow features to {output_file}")

        except Exception as e:
            print(f"Error processing {file_name}: {e}")

if __name__ == "__main__":
    build_labeled_dataset()
