import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
from tqdm import tqdm

# Configuration
EXTRACTED_DATA_DIR = "extracted_features"
OUTPUT_DIR = "analysis_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def analyze_dataset():
    print(f"Searching for extracted features in {EXTRACTED_DATA_DIR}...")
    csv_files = glob.glob(os.path.join(EXTRACTED_DATA_DIR, "*.csv"))
    
    if not csv_files:
        print("No CSV files found. Please run extraction first.")
        return

    for file_path in tqdm(csv_files, desc="Processing files"):
        file_name = os.path.basename(file_path)
        print(f"Analyzing {file_name}...")
        
        try:
            # Load with specific columns to save memory if needed
            df = pd.read_csv(file_path)
            
            # 1. Packet Distribution by Protocol
            plt.figure(figsize=(10, 6))
            sns.countplot(data=df, x='ip.proto')
            plt.title(f"Protocol Distribution - {file_name}")
            plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_protocols.png"))
            plt.close()

            # 2. Packet Size Distribution
            plt.figure(figsize=(10, 6))
            df['frame.len'].hist(bins=100)
            plt.title(f"Packet Size Distribution - {file_name}")
            plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_packet_sizes.png"))
            plt.close()

            # 3. Packet Rate (if time relative exists)
            if 'frame.time_relative' in df.columns:
                df['time_bin'] = df['frame.time_relative'].round()
                rate = df.groupby('time_bin').size()
                plt.figure(figsize=(10, 6))
                rate.plot()
                plt.title(f"Packet Rate over Time - {file_name}")
                plt.savefig(os.path.join(OUTPUT_DIR, f"{file_name}_packet_rate.png"))
                plt.close()

        except Exception as e:
            print(f"Error processing {file_name}: {e}")

if __name__ == "__main__":
    analyze_dataset()
